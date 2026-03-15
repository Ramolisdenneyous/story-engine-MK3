import copy
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from secrets import randbelow

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import settings
from .game_data import (
    ADVENTURES,
    CLASSES,
    DEFAULT_IMAGE_FILE,
    MONSTERS,
    PLAYER_NARRATIVE_LENSES,
    PLAYERS,
    VALASKA_PRESET_ID,
    VALASKA_SYSTEM_PROMPT,
)
from .llm import get_provider, log_artifact
from .models import Event, EventKind, EventRole, MemoryBlock, MemoryBlockType, NarrativeDraft, Session as SessionModel, SessionState, Tab1Inputs

DICE_RE = re.compile(r"^\s*(\d{1,3})\s*d\s*(4|6|8|10|12|20)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)
MARKER_RE = re.compile(r"^(DAMAGE_TAKEN|HEALING_RECEIVED|STATUS_GAINED|STATUS_LOST|INVENTORY_GAINED|INVENTORY_LOST):\s*(.+)$")
VALID_DICE_SIDES = {4, 6, 8, 10, 12, 20}
SLOT_COLORS = {1: "red", 2: "orange", 3: "yellow", 4: "green"}
ASSET_DIR = Path("/app/docs/images")
OPENING_TRANSCRIPT = (
    "Welcome to Valaska, the bitter north at the very edge of the known world. Endless forests of black pine stretch beneath "
    "iron-gray skies, and the wind carries the bite of distant glaciers.\n\n"
    "Your party of four adventurers has gathered in the frontier town of Moosehearth, a stubborn settlement of timber lodges "
    "and smoking chimneys clinging to survival against the cold. Tonight you sit inside the Antlers' Rest Inn, a warm refuge "
    "of firelight, rough laughter, and the smell of spiced ale.\n\n"
    "Just moments ago, one of you returned from the town square carrying a freshly pulled notice from the jobs board. The "
    "parchment is still stiff from the cold, promising coin, danger, and opportunity somewhere out in the frozen wilds.\n\n"
    "Adventure calls."
)


def _empty_combat_state() -> dict:
    return {
        "in_combat": False,
        "round": 1,
        "turn_index": 0,
        "initiative_order": [],
        "initiative_values": {},
    }


def _default_generated_image() -> dict:
    return {
        "image_url": asset_url(DEFAULT_IMAGE_FILE),
        "prompt_text": "",
        "last_actor_slot": None,
    }


def asset_url(filename: str) -> str:
    return f"/assets/{filename}"


def _portrait_filename(player_id: str, class_id: str | None = None) -> str:
    if not class_id:
        return f"Player-{player_id}.jpg"
    candidates = [
        f"{player_id}-{class_id}.jpg",
        f"{player_id}-{class_id.lower()}.jpg",
        f"{player_id}-{class_id.capitalize()}.jpg",
    ]
    for candidate in candidates:
        if (ASSET_DIR / candidate).exists():
            return candidate
    return f"Player-{player_id}.jpg"


def _default_name(slot: int) -> str:
    return f"Agent {SLOT_COLORS.get(slot, slot).title()}"


def _class_assignment_for_slot(tab1: Tab1Inputs, slot: int) -> str:
    value = tab1.class_assignments.get(str(slot), tab1.class_assignments.get(slot, ""))
    return value if value in CLASSES else ""


def _player_for_slot(tab1: Tab1Inputs, slot: int) -> str:
    if slot - 1 < len(tab1.selected_player_ids):
        return tab1.selected_player_ids[slot - 1]
    return ""


def _ability_modifiers(scores: dict[str, int]) -> dict[str, int]:
    return {key: (value - 10) // 2 for key, value in scores.items()}


def _party_member(slot: int, player_id: str, class_id: str, state: dict | None = None) -> dict:
    player = PLAYERS[player_id]
    class_data = CLASSES[class_id]
    member_state = state or {}
    return {
        "slot": slot,
        "player_id": player_id,
        "player_name": player["name"],
        "class_id": class_id,
        "portrait_url": asset_url(_portrait_filename(player_id, class_id)),
        "base_portrait_url": asset_url(_portrait_filename(player_id)),
        "race": player["race"],
        "archetype": player["archetype"],
        "keywords": player["keywords"],
        "armor_class": class_data["armor_class"],
        "hp_max": class_data["hp_max"],
        "hp_current": member_state.get("hp_current", class_data["hp_max"]),
        "status_effects": member_state.get("status_effects", []),
        "inventory": member_state.get("inventory", list(class_data["inventory"])),
        "initiative": member_state.get("initiative"),
    }


def create_session(db: Session) -> SessionModel:
    session = SessionModel(
        state=SessionState.DRAFT_TAB1,
        prompt_index=0,
        last_summarized_prompt_index=0,
        selected_agent_slots=[1, 2, 3, 4],
        agent_names={str(slot): _default_name(slot) for slot in range(1, 5)},
        combat_state=_empty_combat_state(),
        generated_image=_default_generated_image(),
    )
    db.add(session)
    db.flush()
    db.add(
        Tab1Inputs(
            session_id=session.session_id,
            world_text=VALASKA_SYSTEM_PROMPT,
            chapter_text="",
            agent_identity_text_by_slot={},
            preset_id=VALASKA_PRESET_ID,
            adventure_id="",
            selected_player_ids=[],
            class_assignments={},
        )
    )
    db.commit()
    db.refresh(session)
    return session


def get_session_or_404(db: Session, session_id: str) -> SessionModel:
    session = db.get(SessionModel, session_id)
    if not session:
        raise ValueError("Session not found")
    return session


def get_tab1_or_create(db: Session, session_id: str) -> Tab1Inputs:
    tab1 = db.get(Tab1Inputs, session_id)
    if not tab1:
        tab1 = Tab1Inputs(
            session_id=session_id,
            world_text=VALASKA_SYSTEM_PROMPT,
            chapter_text="",
            agent_identity_text_by_slot={},
            preset_id=VALASKA_PRESET_ID,
            adventure_id="",
            selected_player_ids=[],
            class_assignments={},
        )
        db.add(tab1)
        db.flush()
    return tab1


def save_tab1(db: Session, session_id: str, payload: dict) -> tuple[SessionModel, Tab1Inputs]:
    session = get_session_or_404(db, session_id)
    if session.tab1_locked:
        raise ValueError("Tab1 is locked")
    if session.state != SessionState.DRAFT_TAB1:
        raise ValueError("Tab1 edits allowed only in DRAFT_TAB1")

    tab1 = get_tab1_or_create(db, session_id)
    tab1.preset_id = VALASKA_PRESET_ID
    adventure_id = payload.get("adventure_id", "")
    if adventure_id and adventure_id not in ADVENTURES:
        raise ValueError("Unknown adventure_id")
    tab1.adventure_id = adventure_id
    tab1.chapter_text = adventure_id

    selected_player_ids = payload.get("selected_player_ids", [])
    if len(selected_player_ids) != len(set(selected_player_ids)):
        raise ValueError("Players must be unique")
    if len(selected_player_ids) > 4:
        raise ValueError("Exactly four players maximum")
    for player_id in selected_player_ids:
        if player_id not in PLAYERS:
            raise ValueError("Unknown player_id")
    tab1.selected_player_ids = selected_player_ids[:4]

    raw_assignments = payload.get("class_assignments", {})
    class_assignments: dict[str, str] = {}
    for slot in range(1, min(len(tab1.selected_player_ids), 4) + 1):
        class_id = raw_assignments.get(str(slot), raw_assignments.get(slot, ""))
        if class_id:
            if class_id not in CLASSES:
                raise ValueError("Unknown class_id")
            class_assignments[str(slot)] = class_id
    tab1.class_assignments = class_assignments

    session.selected_agent_slots = [1, 2, 3, 4]
    session.agent_names = {str(slot): _default_name(slot) for slot in range(1, 5)}
    for slot in range(1, len(tab1.selected_player_ids) + 1):
        session.agent_names[str(slot)] = PLAYERS[tab1.selected_player_ids[slot - 1]]["name"]

    db.commit()
    db.refresh(session)
    db.refresh(tab1)
    return session, tab1


def _validate_start_ready(tab1: Tab1Inputs) -> None:
    if not tab1.adventure_id:
        raise ValueError("adventure_id is required")
    if len(tab1.selected_player_ids) != 4:
        raise ValueError("Exactly 4 players must be selected")
    for slot in range(1, 5):
        if _class_assignment_for_slot(tab1, slot) not in CLASSES:
            raise ValueError("All 4 classes must be selected")


def _current_memory_blocks(db: Session, session_id: str) -> list[MemoryBlock]:
    return db.execute(
        select(MemoryBlock).where(MemoryBlock.session_id == session_id).order_by(MemoryBlock.created_at.asc())
    ).scalars().all()


def _recent_events(db: Session, session: SessionModel) -> list[Event]:
    from_prompt = max(1, session.prompt_index - 7)
    to_prompt = max(0, session.prompt_index - 1)
    if to_prompt < from_prompt:
        return []
    return db.execute(
        select(Event)
        .where(
            Event.session_id == session.session_id,
            Event.prompt_index >= from_prompt,
            Event.prompt_index <= to_prompt,
            Event.kind == EventKind.TRANSCRIPT,
        )
        .order_by(Event.prompt_index.asc(), Event.created_at.asc())
    ).scalars().all()


def _build_character_payload(db: Session, session: SessionModel, agent_slot: int, user_text: str) -> dict:
    tab1 = get_tab1_or_create(db, session.session_id)
    player_id = _player_for_slot(tab1, agent_slot)
    class_id = _class_assignment_for_slot(tab1, agent_slot)
    player = PLAYERS[player_id]
    class_data = CLASSES[class_id]
    memory_blocks = _current_memory_blocks(db, session.session_id)
    recent_events = _recent_events(db, session)
    return {
        "agent_identity": {
            "slot": agent_slot,
            "name": player["name"],
            "player_prompt": player["display_text"],
            "archetype": player["archetype"],
            "gender": player["gender"],
            "race": player["race"],
        },
        "class_sheet": {
            **class_data,
            "proficiency_bonus": 2,
            "ability_modifiers": _ability_modifiers(class_data["ability_scores"]),
        },
        "structured_memory": [
            {
                "type": block.type.value,
                "from_prompt_index": block.from_prompt_index,
                "to_prompt_index": block.to_prompt_index,
                "json_payload": block.json_payload,
            }
            for block in memory_blocks
        ],
        "recent_context": [
            {
                "prompt_index": event.prompt_index,
                "role": event.role.value,
                "agent_slot": event.agent_slot,
                "agent_name": session.agent_names.get(str(event.agent_slot), None) if event.agent_slot else None,
                "text": event.text,
            }
            for event in recent_events
        ],
        "user_prompt": user_text,
    }


def lock_tab1(db: Session, session_id: str) -> SessionModel:
    provider = get_provider()
    session = get_session_or_404(db, session_id)
    if session.state != SessionState.DRAFT_TAB1:
        raise ValueError("Session cannot be locked from current state")
    tab1 = get_tab1_or_create(db, session_id)
    _validate_start_ready(tab1)

    session.state = SessionState.LOCKING
    db.flush()

    party = []
    for slot in range(1, 5):
        player_id = _player_for_slot(tab1, slot)
        class_id = _class_assignment_for_slot(tab1, slot)
        party.append({"slot": slot, "player_id": player_id, "player_name": PLAYERS[player_id]["name"], "class_id": class_id})

    payload = {
        "setting": VALASKA_SYSTEM_PROMPT,
        "adventure": ADVENTURES[tab1.adventure_id],
        "players": [PLAYERS[player_id] for player_id in tab1.selected_player_ids],
        "party": party,
    }
    text = provider.generate("agent0", settings.llm_model_summary, payload)
    log_artifact(db, session_id, "agent0", settings.llm_model_summary, payload, text, provider.provider_name)
    db.add(
        MemoryBlock(
            session_id=session_id,
            type=MemoryBlockType.WORLD_CHAPTER_LOCK,
            from_prompt_index=0,
            to_prompt_index=0,
            json_payload={
                "summary": text,
                "preset_id": VALASKA_PRESET_ID,
                "world_text": VALASKA_SYSTEM_PROMPT,
                "adventure": ADVENTURES[tab1.adventure_id],
                "agent_names": session.agent_names,
                "party": party,
            },
        )
    )

    session.tab1_locked = True
    session.prompt_index = 0
    session.last_summarized_prompt_index = 0
    session.state = SessionState.ACTIVE
    session.combat_state = _empty_combat_state()
    session.generated_image = _default_generated_image()
    session.selected_narrative_player_id = tab1.selected_player_ids[0]
    db.add(
        Event(
            session_id=session_id,
            prompt_index=0,
            role=EventRole.SYSTEM,
            kind=EventKind.TRANSCRIPT,
            agent_slot=None,
            text=OPENING_TRANSCRIPT,
            json_payload={"source": "opening_transcript"},
        )
    )

    db.commit()
    db.refresh(session)
    return session


def _run_summarization(db: Session, session: SessionModel, to_prompt_index: int) -> bool:
    if to_prompt_index <= session.last_summarized_prompt_index:
        return False
    provider = get_provider()
    from_idx = session.last_summarized_prompt_index + 1
    events = db.execute(
        select(Event)
        .where(
            Event.session_id == session.session_id,
            Event.prompt_index >= from_idx,
            Event.prompt_index <= to_prompt_index,
        )
        .order_by(Event.prompt_index.asc(), Event.created_at.asc())
    ).scalars().all()
    payload = {
        "from_prompt_index": from_idx,
        "to_prompt_index": to_prompt_index,
        "events": [
            {
                "prompt_index": event.prompt_index,
                "role": event.role.value,
                "kind": event.kind.value,
                "agent_slot": event.agent_slot,
                "text": event.text,
                "json_payload": event.json_payload,
            }
            for event in events
        ],
        "combat_state": session.combat_state,
    }
    try:
        output = provider.generate("agent8", settings.llm_model_summary, payload)
        log_artifact(db, session.session_id, "agent8", settings.llm_model_summary, payload, output, provider.provider_name)
        db.add(
            MemoryBlock(
                session_id=session.session_id,
                type=MemoryBlockType.TURN_DELTA,
                from_prompt_index=from_idx,
                to_prompt_index=to_prompt_index,
                json_payload={"summary": output, "event_count": len(events), "combat_state": copy.deepcopy(session.combat_state)},
            )
        )
        session.last_summarized_prompt_index = to_prompt_index
        return True
    except Exception as exc:
        fallback_summary = (
            f"Fallback summary for prompts {from_idx}-{to_prompt_index}. "
            f"Captured {len(events)} events while remote summarization was unavailable ({type(exc).__name__})."
        )
        db.add(
            MemoryBlock(
                session_id=session.session_id,
                type=MemoryBlockType.TURN_DELTA,
                from_prompt_index=from_idx,
                to_prompt_index=to_prompt_index,
                json_payload={
                    "summary": fallback_summary,
                    "event_count": len(events),
                    "combat_state": copy.deepcopy(session.combat_state),
                    "summary_source": "fallback",
                },
            )
        )
        session.last_summarized_prompt_index = to_prompt_index
        return True


def _strip_markers(agent_text: str) -> tuple[str, list[tuple[str, str]]]:
    clean_lines = []
    markers: list[tuple[str, str]] = []
    for line in agent_text.splitlines():
        match = MARKER_RE.match(line.strip())
        if match:
            markers.append((match.group(1), match.group(2).strip()))
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip(), markers


def _append_system_event(db: Session, session_id: str, prompt_index: int, kind: EventKind, text: str, payload: dict) -> None:
    db.add(
        Event(
            session_id=session_id,
            prompt_index=prompt_index,
            role=EventRole.SYSTEM,
            kind=kind,
            agent_slot=None,
            text=text,
            json_payload=payload,
        )
    )


def _apply_markers(db: Session, session: SessionModel, agent_slot: int, prompt_index: int, markers: list[tuple[str, str]]) -> None:
    name = session.agent_names.get(str(agent_slot), _default_name(agent_slot))
    for marker, value in markers:
        if marker == "DAMAGE_TAKEN" and value.isdigit():
            _append_state_change(db, session, prompt_index, agent_slot, "damage", amount=int(value), source="marker")
        elif marker == "HEALING_RECEIVED" and value.isdigit():
            _append_state_change(db, session, prompt_index, agent_slot, "healing", amount=int(value), source="marker")
        elif marker == "STATUS_GAINED":
            _append_state_change(db, session, prompt_index, agent_slot, "status_add", value=value, source="marker")
        elif marker == "STATUS_LOST":
            _append_state_change(db, session, prompt_index, agent_slot, "status_remove", value=value, source="marker")
        elif marker == "INVENTORY_GAINED":
            _append_state_change(db, session, prompt_index, agent_slot, "inventory_add", value=value, source="marker")
        elif marker == "INVENTORY_LOST":
            _append_state_change(db, session, prompt_index, agent_slot, "inventory_remove", value=value, source="marker")


def _append_state_change(
    db: Session,
    session: SessionModel,
    prompt_index: int,
    slot: int,
    kind: str,
    amount: int = 0,
    value: str = "",
    source: str = "unknown",
) -> None:
    name = session.agent_names.get(str(slot), _default_name(slot))
    if kind == "damage" and amount > 0:
        _append_system_event(db, session.session_id, prompt_index, EventKind.DAMAGE_APPLIED, f"{name} takes {amount} damage.", {"target_slot": slot, "amount": amount, "source": source})
    elif kind == "healing" and amount > 0:
        _append_system_event(db, session.session_id, prompt_index, EventKind.DAMAGE_APPLIED, f"{name} heals {amount} HP.", {"target_slot": slot, "amount": -amount, "source": source})
    elif kind == "status_add" and value:
        _append_system_event(db, session.session_id, prompt_index, EventKind.CONDITION_ADDED, f"{name} gains status: {value}.", {"target_slot": slot, "status": value, "source": source})
    elif kind == "status_remove" and value:
        _append_system_event(db, session.session_id, prompt_index, EventKind.CONDITION_REMOVED, f"{name} loses status: {value}.", {"target_slot": slot, "status": value, "source": source})
    elif kind == "inventory_add" and value:
        _append_system_event(db, session.session_id, prompt_index, EventKind.INVENTORY_GAINED, f"{name} gains {value}.", {"target_slot": slot, "item": value, "source": source})
    elif kind == "inventory_remove" and value:
        _append_system_event(db, session.session_id, prompt_index, EventKind.INVENTORY_LOST, f"{name} loses {value}.", {"target_slot": slot, "item": value, "source": source})


def _collect_target_slots(session: SessionModel, agent_slot: int, lowered: str) -> set[int]:
    named_slots = {
        int(slot_text)
        for slot_text, name in session.agent_names.items()
        if name and re.search(rf"\b{re.escape(name.lower())}\b", lowered)
    }
    if re.search(r"\b(?:everyone|everybody|all of you|you all|the group of you|each of you|all take)\b", lowered):
        return named_slots or {int(slot_text) for slot_text in session.agent_names.keys()}
    if named_slots:
        return named_slots
    if re.search(r"\byou\b", lowered):
        return {agent_slot}
    return set()


def _extract_gm_state_events(db: Session, session: SessionModel, agent_slot: int, prompt_index: int, user_text: str) -> None:
    lowered = user_text.lower()
    targets = _collect_target_slots(session, agent_slot, lowered)

    damage_match = re.search(r"\b(?:take|takes|suffer|suffers|for|deals?)\s+(\d+)\s+(?:points?\s+of\s+)?damage\b", lowered)
    if damage_match and targets:
        amount = int(damage_match.group(1))
        for slot in sorted(targets):
            _append_state_change(db, session, prompt_index, slot, "damage", amount=amount, source="gm_parser")

    heal_match = re.search(r"\b(?:heal|heals|recover|recovers|regain|regains)\s+(\d+)\s*(?:hp|hit points)?\b", lowered)
    if heal_match and targets:
        amount = int(heal_match.group(1))
        for slot in sorted(targets):
            _append_state_change(db, session, prompt_index, slot, "healing", amount=amount, source="gm_parser")

    gain_match = re.search(
        r"\b(?:gifted|gets?|finds?|receives?|gains?|given)(?:\s+\w+){0,6}\s+(?:an?|one|1)\s+([a-z][a-z\s'-]+?)(?:[,.!]|$)",
        lowered,
    )
    if gain_match and targets:
        item = gain_match.group(1).strip().title()
        for slot in sorted(targets):
            _append_state_change(db, session, prompt_index, slot, "inventory_add", value=item, source="gm_parser")

    lose_match = re.search(r"\b(?:loses?|drop|drops|spends?)\s+(?:an?|one|1)\s+([a-z][a-z\s'-]+?)(?:[,.!]|$)", lowered)
    if lose_match and targets:
        item = lose_match.group(1).strip().title()
        for slot in sorted(targets):
            _append_state_change(db, session, prompt_index, slot, "inventory_remove", value=item, source="gm_parser")


def _advance_turn_if_in_combat(session: SessionModel) -> None:
    combat = copy.deepcopy(session.combat_state or _empty_combat_state())
    if not combat.get("in_combat") or not combat.get("initiative_order"):
        session.combat_state = combat
        return
    combat["turn_index"] += 1
    if combat["turn_index"] >= len(combat["initiative_order"]):
        combat["round"] += 1
        combat["turn_index"] = 0
    session.combat_state = combat


def prompt_agent(db: Session, session_id: str, agent_slot: int, user_text: str) -> tuple[SessionModel, Event, Event, bool]:
    provider = get_provider()
    session = get_session_or_404(db, session_id)
    if session.state != SessionState.ACTIVE:
        raise ValueError("Session is not ACTIVE")
    if agent_slot not in session.selected_agent_slots:
        raise ValueError("Agent slot not selected for this session")

    session.prompt_index += 1
    user_event = Event(
        session_id=session_id,
        prompt_index=session.prompt_index,
        role=EventRole.USER,
        kind=EventKind.TRANSCRIPT,
        agent_slot=None,
        text=f"GM: {user_text}",
        json_payload={},
    )
    db.add(user_event)
    db.flush()
    _extract_gm_state_events(db, session, agent_slot, session.prompt_index, user_text)

    agent_payload = _build_character_payload(db, session, agent_slot, user_text)
    agent_text_raw = provider.generate("agent_character", settings.llm_model_character, agent_payload)
    log_artifact(db, session_id, "agent_character", settings.llm_model_character, agent_payload, agent_text_raw, provider.provider_name)
    agent_text, markers = _strip_markers(agent_text_raw)
    agent_event = Event(
        session_id=session_id,
        prompt_index=session.prompt_index,
        role=EventRole.AGENT,
        kind=EventKind.TRANSCRIPT,
        agent_slot=agent_slot,
        text=agent_text,
        json_payload={},
    )
    db.add(agent_event)
    _apply_markers(db, session, agent_slot, session.prompt_index, markers)
    _append_system_event(db, session_id, session.prompt_index, EventKind.TURN_ENDED, f"Turn ended for {session.agent_names.get(str(agent_slot), _default_name(agent_slot))}.", {"agent_slot": agent_slot})
    _advance_turn_if_in_combat(session)

    summary_triggered = False
    if session.prompt_index % settings.chunk_size_prompts == 0:
        session.state = SessionState.SUMMARIZING
        summary_triggered = _run_summarization(db, session, session.prompt_index)
        session.state = SessionState.ACTIVE

    session.generated_image = {**session.generated_image, "last_actor_slot": agent_slot}
    db.commit()
    db.refresh(session)
    db.refresh(user_event)
    db.refresh(agent_event)
    return session, user_event, agent_event, summary_triggered


def end_chapter(db: Session, session_id: str) -> SessionModel:
    session = get_session_or_404(db, session_id)
    if session.state != SessionState.ACTIVE:
        raise ValueError("End chapter allowed only from ACTIVE")
    if session.last_summarized_prompt_index < session.prompt_index:
        session.state = SessionState.SUMMARIZING
        _run_summarization(db, session, session.prompt_index)
    session.state = SessionState.ENDED
    db.commit()
    db.refresh(session)
    return session


def save_narrative_agent(db: Session, session_id: str, selected_player_id: str) -> SessionModel:
    session = get_session_or_404(db, session_id)
    tab1 = get_tab1_or_create(db, session_id)
    if selected_player_id not in tab1.selected_player_ids:
        raise ValueError("Narrative player must be one of the selected players")
    session.selected_narrative_player_id = selected_player_id
    session.narrative_agent_definition_text = PLAYER_NARRATIVE_LENSES[selected_player_id]
    db.commit()
    db.refresh(session)
    return session


def build_narrative(db: Session, session_id: str) -> NarrativeDraft:
    provider = get_provider()
    session = get_session_or_404(db, session_id)
    tab1 = get_tab1_or_create(db, session_id)
    if session.state != SessionState.ENDED:
        raise ValueError("Build narrative allowed only in ENDED state")
    if session.selected_narrative_player_id not in tab1.selected_player_ids:
        raise ValueError("Select a narrative player first")

    session.state = SessionState.NARRATING
    events = db.execute(select(Event).where(Event.session_id == session_id).order_by(Event.prompt_index.asc(), Event.created_at.asc())).scalars().all()
    blocks = _current_memory_blocks(db, session_id)
    payload = {
        "selected_player_id": session.selected_narrative_player_id,
        "memory_blocks": [
            {
                "block_id": block.block_id,
                "type": block.type.value,
                "from_prompt_index": block.from_prompt_index,
                "to_prompt_index": block.to_prompt_index,
                "json_payload": block.json_payload,
            }
            for block in blocks
        ],
        "events": [
            {
                "prompt_index": event.prompt_index,
                "role": event.role.value,
                "kind": event.kind.value,
                "agent_slot": event.agent_slot,
                "text": event.text,
                "json_payload": event.json_payload,
            }
            for event in events
        ],
        "adventure": ADVENTURES.get(tab1.adventure_id),
    }
    try:
        output = provider.generate("agent9", settings.llm_model_narrative, payload)
        narrative_source = provider.provider_name
        log_artifact(db, session_id, "agent9", settings.llm_model_narrative, payload, output, provider.provider_name)
    except httpx.HTTPStatusError:
        output = _build_narrative_fallback(session, tab1, events, blocks)
        narrative_source = "fallback"
    draft = NarrativeDraft(
        session_id=session_id,
        narrative_agent_definition_text=session.narrative_agent_definition_text,
        source_snapshot={
            "max_prompt_index_used": session.prompt_index,
            "memory_block_ids_used": [block.block_id for block in blocks],
            "narrative_source": narrative_source,
        },
        chapter_text=output,
    )
    db.add(draft)
    session.state = SessionState.ENDED
    db.commit()
    db.refresh(draft)
    return draft


def _build_narrative_fallback(
    session: SessionModel,
    tab1: Tab1Inputs,
    events: list[Event],
    blocks: list[MemoryBlock],
) -> str:
    selected_player_id = session.selected_narrative_player_id
    adventure = ADVENTURES.get(tab1.adventure_id) or {}
    class_name = (tab1.class_assignments or {}).get(selected_player_id, "adventurer")
    recent_turns = [event for event in events if event.role in {EventRole.USER, EventRole.AGENT}][-10:]
    transcript_lines: list[str] = []
    for event in recent_turns:
        if event.role == EventRole.USER:
            transcript_lines.append(f"GM: {event.text}")
        elif event.role == EventRole.AGENT:
            transcript_lines.append(event.text.strip())

    summary_lines: list[str] = []
    for block in blocks[-3:]:
        payload = block.json_payload or {}
        summary = payload.get("summary")
        if isinstance(summary, str) and summary.strip():
            summary_lines.append(summary.strip())

    parts = [
        f"Adventure recap from {selected_player_id}'s point of view.",
        f"{selected_player_id} traveled as the party's {class_name} on {adventure.get('title', 'their Valaska mission')}.",
    ]
    if summary_lines:
        parts.append("Structured memory highlights:")
        parts.extend(summary_lines)
    if transcript_lines:
        parts.append("Recent key moments:")
        parts.extend(transcript_lines)
    parts.append(
        "This fallback chapter was assembled locally because the narrative model was temporarily unavailable."
    )
    return "\n\n".join(parts)


def reset_session(db: Session, session_id: str) -> SessionModel:
    session = get_session_or_404(db, session_id)
    session.state = SessionState.RESETTING
    db.flush()
    db.execute(delete(Event).where(Event.session_id == session_id))
    db.execute(delete(MemoryBlock).where(MemoryBlock.session_id == session_id))
    db.execute(delete(NarrativeDraft).where(NarrativeDraft.session_id == session_id))

    tab1 = get_tab1_or_create(db, session_id)
    tab1.world_text = VALASKA_SYSTEM_PROMPT
    tab1.chapter_text = ""
    tab1.agent_identity_text_by_slot = {}
    tab1.preset_id = VALASKA_PRESET_ID
    tab1.adventure_id = ""
    tab1.selected_player_ids = []
    tab1.class_assignments = {}

    session.state = SessionState.DRAFT_TAB1
    session.prompt_index = 0
    session.last_summarized_prompt_index = 0
    session.tab1_locked = False
    session.selected_agent_slots = [1, 2, 3, 4]
    session.agent_names = {str(slot): _default_name(slot) for slot in range(1, 5)}
    session.narrative_agent_definition_text = ""
    session.selected_narrative_player_id = ""
    session.combat_state = _empty_combat_state()
    session.generated_image = _default_generated_image()

    db.commit()
    db.refresh(session)
    return session


def perform_dice_roll(formula: str, label: str = "", roller_id: str = "unknown") -> dict:
    match = DICE_RE.match(formula or "")
    if not match:
        return {"error": {"code": "invalid_formula", "message": "Formula must look like NdM+K using d4/d6/d8/d10/d12/d20."}}
    dice_count = int(match.group(1))
    dice_sides = int(match.group(2))
    modifier_raw = match.group(3) or ""
    modifier = int(modifier_raw.replace(" ", "")) if modifier_raw else 0
    if dice_count < 1 or dice_count > 100 or dice_sides not in VALID_DICE_SIDES:
        return {"error": {"code": "invalid_formula", "message": "Dice count or sides are out of bounds."}}
    rolls = [randbelow(dice_sides) + 1 for _ in range(dice_count)]
    timestamp = datetime.now(timezone.utc)
    return {
        "formula": formula.replace(" ", ""),
        "dice_count": dice_count,
        "dice_sides": dice_sides,
        "rolls": rolls,
        "modifier": modifier,
        "total": sum(rolls) + modifier,
        "label": label,
        "roller_id": roller_id,
        "timestamp": timestamp.isoformat(),
        "roll_id": str(uuid.uuid4()),
    }


def roll_dice_for_session(db: Session, session_id: str, formula: str, label: str = "", roller_id: str = "unknown") -> dict:
    session = get_session_or_404(db, session_id)
    result = perform_dice_roll(formula, label, roller_id)
    if "error" in result:
        raise ValueError(result["error"]["message"])
    db.add(
        Event(
            session_id=session_id,
            prompt_index=session.prompt_index,
            role=EventRole.SYSTEM,
            kind=EventKind.DICE_ROLL,
            agent_slot=None,
            text=f"{label or formula}: {result['total']}",
            json_payload=result,
        )
    )
    db.commit()
    return result


def roll_dice_batch_for_session(db: Session, session_id: str, rolls: list[dict]) -> list[dict]:
    return [roll_dice_for_session(db, session_id, item.get("formula", ""), item.get("label", ""), item.get("roller_id", "unknown")) for item in rolls]


def roll_initiative(db: Session, session_id: str) -> dict:
    session = get_session_or_404(db, session_id)
    tab1 = get_tab1_or_create(db, session_id)
    if not session.tab1_locked:
        raise ValueError("Lock Tab1 before rolling initiative")

    rolls = []
    initiative_values: dict[str, int] = {}
    for slot in range(1, 5):
        player_id = _player_for_slot(tab1, slot)
        class_id = _class_assignment_for_slot(tab1, slot)
        dex = CLASSES[class_id]["ability_scores"]["DEX"]
        modifier = (dex - 10) // 2
        formula = f"1d20+{modifier}" if modifier >= 0 else f"1d20{modifier}"
        result = roll_dice_for_session(db, session_id, formula, f"Initiative: {PLAYERS[player_id]['name']}", f"Player:{player_id}")
        rolls.append(result)
        initiative_values[f"pc:{slot}"] = result["total"]

    ordered = sorted(initiative_values.items(), key=lambda item: (-item[1], item[0]))
    session.combat_state = {
        "in_combat": True,
        "round": 1,
        "turn_index": 0,
        "initiative_order": [combatant_id for combatant_id, _ in ordered],
        "initiative_values": initiative_values,
    }
    db.add(
        Event(
            session_id=session_id,
            prompt_index=session.prompt_index,
            role=EventRole.SYSTEM,
            kind=EventKind.INITIATIVE_SET,
            agent_slot=None,
            text="Initiative order updated.",
            json_payload=copy.deepcopy(session.combat_state),
        )
    )
    db.commit()
    return {"combat_state": session.combat_state, "rolls": rolls}


def _reference_image_bytes(tab1: Tab1Inputs, last_actor_slot: int | None) -> bytes | None:
    if not last_actor_slot:
        return None
    player_id = _player_for_slot(tab1, last_actor_slot)
    class_id = _class_assignment_for_slot(tab1, last_actor_slot)
    if not player_id or not class_id:
        return None
    path = ASSET_DIR / _portrait_filename(player_id, class_id)
    if not path.exists():
        return None
    return path.read_bytes()


def generate_scene_image(db: Session, session_id: str) -> dict:
    session = get_session_or_404(db, session_id)
    provider = get_provider()
    tab1 = get_tab1_or_create(db, session_id)
    payload = {
        "structured_memory": [
            {
                "type": block.type.value,
                "from_prompt_index": block.from_prompt_index,
                "to_prompt_index": block.to_prompt_index,
                "json_payload": block.json_payload,
            }
            for block in _current_memory_blocks(db, session_id)
        ],
        "recent_context": [
            {"prompt_index": event.prompt_index, "role": event.role.value, "agent_slot": event.agent_slot, "text": event.text}
            for event in _recent_events(db, session)
        ],
    }
    prompt_text = provider.generate("agent10", settings.llm_model_summary, payload)
    log_artifact(db, session_id, "agent10", settings.llm_model_summary, payload, prompt_text, provider.provider_name)
    try:
        image_url = provider.generate_image(prompt_text, _reference_image_bytes(tab1, session.generated_image.get("last_actor_slot")))
    except Exception:
        image_url = asset_url(DEFAULT_IMAGE_FILE)
    if image_url == "mock://generated-image":
        image_url = asset_url(DEFAULT_IMAGE_FILE)
    session.generated_image = {"image_url": image_url, "prompt_text": prompt_text, "last_actor_slot": session.generated_image.get("last_actor_slot")}
    db.add(
        Event(
            session_id=session_id,
            prompt_index=session.prompt_index,
            role=EventRole.SYSTEM,
            kind=EventKind.IMAGE_GENERATED,
            agent_slot=None,
            text="Scene image updated.",
            json_payload=copy.deepcopy(session.generated_image),
        )
    )
    db.commit()
    return session.generated_image


def derive_party_state(db: Session, session_id: str) -> dict[str, dict]:
    session = get_session_or_404(db, session_id)
    tab1 = get_tab1_or_create(db, session_id)
    state = {}
    for slot in range(1, 5):
        player_id = _player_for_slot(tab1, slot)
        class_id = _class_assignment_for_slot(tab1, slot)
        if not player_id or not class_id:
            continue
        class_data = CLASSES[class_id]
        state[str(slot)] = {
            "hp_current": class_data["hp_max"],
            "status_effects": [],
            "inventory": list(class_data["inventory"]),
            "initiative": session.combat_state.get("initiative_values", {}).get(f"pc:{slot}"),
        }

    events = db.execute(select(Event).where(Event.session_id == session_id).order_by(Event.created_at.asc())).scalars().all()
    seen_state_events: set[tuple] = set()
    for event in events:
        payload = event.json_payload or {}
        slot = payload.get("target_slot")
        if slot is None:
            continue
        key = str(slot)
        if key not in state:
            continue
        dedupe_key = None
        if event.kind == EventKind.DAMAGE_APPLIED:
            dedupe_key = (event.prompt_index, event.kind.value, slot, int(payload.get("amount", 0)))
        elif event.kind in {EventKind.CONDITION_ADDED, EventKind.CONDITION_REMOVED}:
            dedupe_key = (event.prompt_index, event.kind.value, slot, payload.get("status", ""))
        elif event.kind in {EventKind.INVENTORY_GAINED, EventKind.INVENTORY_LOST}:
            dedupe_key = (event.prompt_index, event.kind.value, slot, payload.get("item", ""))
        if dedupe_key is not None:
            if dedupe_key in seen_state_events:
                continue
            seen_state_events.add(dedupe_key)
        if event.kind == EventKind.DAMAGE_APPLIED:
            amount = int(payload.get("amount", 0))
            hp_max = CLASSES[_class_assignment_for_slot(tab1, int(slot))]["hp_max"]
            state[key]["hp_current"] = max(0, min(state[key]["hp_current"] - amount, hp_max))
        elif event.kind == EventKind.CONDITION_ADDED:
            status = payload.get("status", "")
            if status and status not in state[key]["status_effects"]:
                state[key]["status_effects"].append(status)
        elif event.kind == EventKind.CONDITION_REMOVED:
            status = payload.get("status", "")
            state[key]["status_effects"] = [item for item in state[key]["status_effects"] if item != status]
        elif event.kind == EventKind.INVENTORY_GAINED:
            item = payload.get("item", "")
            if item:
                state[key]["inventory"].append(item)
        elif event.kind == EventKind.INVENTORY_LOST:
            item = payload.get("item", "")
            if item in state[key]["inventory"]:
                state[key]["inventory"].remove(item)
    return state


def get_session_detail(db: Session, session_id: str) -> dict:
    session = get_session_or_404(db, session_id)
    tab1 = get_tab1_or_create(db, session_id)
    events = db.execute(select(Event).where(Event.session_id == session_id).order_by(Event.prompt_index.asc(), Event.created_at.asc())).scalars().all()
    memory_blocks = _current_memory_blocks(db, session_id)
    drafts = db.execute(select(NarrativeDraft).where(NarrativeDraft.session_id == session_id).order_by(NarrativeDraft.created_at.asc())).scalars().all()
    party_state = derive_party_state(db, session_id)
    party = []
    for slot in range(1, 5):
        player_id = _player_for_slot(tab1, slot)
        class_id = _class_assignment_for_slot(tab1, slot)
        if player_id and class_id:
            party.append(_party_member(slot, player_id, class_id, party_state.get(str(slot), {})))
    gm_monsters = [MONSTERS[name] for name in ADVENTURES.get(tab1.adventure_id, {}).get("monsters", [])]
    return {
        "session": session,
        "tab1": tab1,
        "events": events,
        "memory_blocks": memory_blocks,
        "narrative_drafts": drafts,
        "party": party,
        "active_adventure": ADVENTURES.get(tab1.adventure_id),
        "gm_monsters": gm_monsters,
        "image_state": session.generated_image or _default_generated_image(),
    }
