import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, resolveApiUrl } from "./api";

type SessionState = "DRAFT_TAB1" | "LOCKING" | "ACTIVE" | "SUMMARIZING" | "ENDED" | "NARRATING" | "RESETTING";

type Catalog = {
  preset_id: string;
  preset_name: string;
  map_image_url: string;
  adventure_selection_image_url: string;
  default_image_url: string;
  adventures: Adventure[];
  players: PlayerCatalog[];
  classes: ClassCatalog[];
  monsters: Monster[];
};

type Adventure = {
  adventure_id: string;
  title: string;
  description: string;
  objectives: Array<{ id: string; description: string; status: string }>;
  monsters: string[];
};

type PlayerCatalog = {
  player_id: string;
  name: string;
  archetype: string;
  gender: string;
  race: string;
  irl_job: string;
  keywords: string[];
  display_text: string;
  image_url: string;
};

type ClassCatalog = {
  class_id: string;
  name: string;
  role: string;
  armor_class: number;
  hp_max: number;
};

type Monster = {
  monster_id: string;
  ac: number;
  hp: number;
  attack_bonus: number;
  attack_text: string;
};

type CombatState = {
  in_combat: boolean;
  round: number;
  turn_index: number;
  initiative_order: string[];
  initiative_values: Record<string, number>;
};

type PartyMember = {
  slot: number;
  player_id: string;
  player_name: string;
  class_id: string;
  portrait_url: string;
  base_portrait_url: string;
  race: string;
  archetype: string;
  keywords: string[];
  armor_class: number;
  hp_max: number;
  hp_current: number;
  status_effects: string[];
  inventory: string[];
  initiative: number | null;
};

type SessionDetail = {
  session: {
    session_id: string;
    state: SessionState;
    prompt_index: number;
    last_summarized_prompt_index: number;
    tab1_locked: boolean;
    combat_state: CombatState;
    selected_narrative_player_id: string;
  };
  tab1: {
    preset_id: string;
    adventure_id: string;
    selected_player_ids: string[];
    class_assignments: Record<number, string>;
    selected_agent_slots: number[];
    agent_names: Record<number, string>;
    tab1_locked: boolean;
    party: PartyMember[];
    active_adventure: Adventure | null;
  };
  events: Array<{
    event_id: string;
    prompt_index: number;
    role: "user" | "agent" | "system";
    kind: string;
    agent_slot: number | null;
    text: string;
    json_payload: Record<string, unknown>;
    created_at: string;
  }>;
  memory_blocks: Array<{
    block_id: string;
    type: string;
    from_prompt_index: number;
    to_prompt_index: number;
    json_payload: Record<string, unknown>;
  }>;
  narrative_drafts: Array<{ draft_id: string; chapter_text: string }>;
  image_state: { image_url: string; prompt_text: string; last_actor_slot: number | null };
  gm_monsters: Monster[];
};

const SLOT_COLORS: Record<number, string> = {
  1: "#f56f7e",
  2: "#ff9e4a",
  3: "#f4cf59",
  4: "#60d48f",
};

const MUSIC_TRACKS = [
  "Citadel of Rusted Banners.mp3",
  "Citadel of Rusted Banners2.mp3",
  "Cursed Village Menu.mp3",
  "Cursed Village Menu2.mp3",
  "Gallows of the Forgotten King.mp3",
  "Gallows of the Forgotten King2.mp3",
  "Torchlit War Map.mp3",
  "Torchlit War Map2.mp3",
].map((fileName) => resolveApiUrl(`/music/${encodeURIComponent(fileName)}`));
const TESTING_PASSWORD = "Rayis1cooldude";

export function App() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [tab, setTab] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [narrativeBuilding, setNarrativeBuilding] = useState(false);
  const [error, setError] = useState("");
  const [adventurePickerOpen, setAdventurePickerOpen] = useState(false);
  const [trackIndex, setTrackIndex] = useState(0);
  const [musicPlaying, setMusicPlaying] = useState(false);
  const [musicMuted, setMusicMuted] = useState(false);
  const [unlocked, setUnlocked] = useState(() => window.sessionStorage.getItem("mk2_unlocked") === "true");
  const [passwordInput, setPasswordInput] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const [adventureId, setAdventureId] = useState("");
  const [selectedPlayerIds, setSelectedPlayerIds] = useState<string[]>([]);
  const [classByPlayer, setClassByPlayer] = useState<Record<string, string>>({});
  const [activeAgentSlot, setActiveAgentSlot] = useState(1);
  const [userPrompt, setUserPrompt] = useState("");
  const [diceFormula, setDiceFormula] = useState("1d20");
  const [diceResult, setDiceResult] = useState("");
  const [selectedNarrativePlayerId, setSelectedNarrativePlayerId] = useState("");

  async function boot() {
    setLoading(true);
    setError("");
    try {
      const [catalogData, created] = await Promise.all([
        api<Catalog>("/catalog"),
        api<{ session_id: string }>("/session", { method: "POST" }),
      ]);
      setCatalog(catalogData);
      setSessionId(created.session_id);
      await refresh(created.session_id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function refresh(id = sessionId) {
    const data = await api<SessionDetail>(`/session/${id}`);
    setDetail(data);
    setAdventureId(data.tab1.adventure_id);
    setSelectedPlayerIds(data.tab1.selected_player_ids);
    const byPlayer: Record<string, string> = {};
    data.tab1.party.forEach((member) => {
      byPlayer[member.player_id] = member.class_id;
    });
    setClassByPlayer(byPlayer);
    setSelectedNarrativePlayerId(data.session.selected_narrative_player_id);
    if (!data.tab1.selected_agent_slots.includes(activeAgentSlot)) {
      setActiveAgentSlot(data.tab1.selected_agent_slots[0] ?? 1);
    }
  }

  useEffect(() => {
    void boot();
  }, []);

  const transcript = useMemo(() => {
    if (!detail) return [];
    return detail.events.filter((event) => event.kind === "transcript");
  }, [detail]);

  useEffect(() => {
    const box = transcriptRef.current;
    if (!box) return;
    box.scrollTop = box.scrollHeight;
  }, [detail?.events.length, detail?.session.prompt_index]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = 0.35;
    audio.muted = musicMuted;
    if (musicPlaying) {
      void audio.play().catch(() => {
        setMusicPlaying(false);
      });
    } else {
      audio.pause();
    }
  }, [trackIndex, musicPlaying, musicMuted]);

  async function toggleMusicPlayback() {
    const audio = audioRef.current;
    if (!audio) return;
    if (musicPlaying) {
      audio.pause();
      setMusicPlaying(false);
      return;
    }
    try {
      audio.muted = musicMuted;
      await audio.play();
      setMusicPlaying(true);
    } catch (e) {
      setError((e as Error).message || "Unable to start music playback.");
    }
  }

  function toggleMusicMuted() {
    const audio = audioRef.current;
    const nextMuted = !musicMuted;
    if (audio) {
      audio.muted = nextMuted;
    }
    setMusicMuted(nextMuted);
  }

  function submitPassword(event: FormEvent) {
    event.preventDefault();
    if (passwordInput === TESTING_PASSWORD) {
      window.sessionStorage.setItem("mk2_unlocked", "true");
      setUnlocked(true);
      setPasswordError("");
      setPasswordInput("");
      return;
    }
    setPasswordError("Incorrect password.");
  }

  const selectedAdventure = useMemo(
    () => catalog?.adventures.find((item) => item.adventure_id === adventureId) ?? null,
    [adventureId, catalog],
  );

  const transcriptChars = transcript.reduce((sum, event) => sum + event.text.length + 1, 0);
  const latestDraft = detail?.narrative_drafts.length ? detail.narrative_drafts[detail.narrative_drafts.length - 1] : null;

  function togglePlayer(playerId: string) {
    setSelectedPlayerIds((current) => {
      if (current.includes(playerId)) {
        const next = current.filter((item) => item !== playerId);
        setClassByPlayer((map) => {
          const copy = { ...map };
          delete copy[playerId];
          return copy;
        });
        return next;
      }
      if (current.length >= 4) return current;
      return [...current, playerId];
    });
  }

  function setPlayerClass(playerId: string, classId: string) {
    setClassByPlayer((current) => ({ ...current, [playerId]: classId }));
  }

  const startReady =
    adventureId !== "" &&
    selectedPlayerIds.length === 4 &&
    selectedPlayerIds.every((playerId) => Boolean(classByPlayer[playerId]));

  async function saveTab1() {
    if (!sessionId) return;
    setLoading(true);
    setError("");
    try {
      const class_assignments = Object.fromEntries(
        selectedPlayerIds.map((playerId, index) => [String(index + 1), classByPlayer[playerId] ?? ""]),
      );
      await api(`/session/${sessionId}/tab1`, {
        method: "PUT",
        body: JSON.stringify({
          preset_id: "valaska",
          adventure_id: adventureId,
          selected_player_ids: selectedPlayerIds,
          class_assignments,
        }),
      });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function startChapter() {
    await saveTab1();
    setLoading(true);
    try {
      await api(`/session/${sessionId}/lock`, { method: "POST" });
      await refresh();
      setTab(2);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function orderedAgentSlots(): number[] {
    const currentDetail = detail;
    if (!currentDetail) return [1, 2, 3, 4];
    if (currentDetail.session.combat_state.in_combat) {
      return currentDetail.session.combat_state.initiative_order
        .map((item) => Number(item.replace("pc:", "")))
        .filter((slot) => Number.isFinite(slot));
    }
    return currentDetail.tab1.selected_agent_slots;
  }

  async function submitPrompt(event: FormEvent) {
    event.preventDefault();
    if (!sessionId || !userPrompt.trim()) return;
    setLoading(true);
    setError("");
    try {
      await api(`/session/${sessionId}/prompt`, {
        method: "POST",
        body: JSON.stringify({ agent_slot: activeAgentSlot, user_text: userPrompt }),
      });
      setUserPrompt("");
      await refresh();
      const order = orderedAgentSlots();
      const index = order.indexOf(activeAgentSlot);
      setActiveAgentSlot(order[(index + 1 + order.length) % order.length] ?? order[0] ?? 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function endChapter() {
    setLoading(true);
    try {
      await api(`/session/${sessionId}/end`, { method: "POST" });
      await refresh();
      setTab(3);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function rollInitiative() {
    setLoading(true);
    try {
      await api(`/session/${sessionId}/roll-initiative`, { method: "POST" });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function rollDice() {
    setLoading(true);
    try {
      const result = await api<{ total: number; rolls: number[]; formula: string }>(`/session/${sessionId}/roll-dice`, {
        method: "POST",
        body: JSON.stringify({ formula: diceFormula, label: `GM roll: ${diceFormula}`, roller_id: "GM" }),
      });
      setDiceResult(`${result.formula}: ${result.rolls.join(", ")} = ${result.total}`);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function generateImage() {
    setImageLoading(true);
    setError("");
    try {
      await api(`/session/${sessionId}/generate-image`, { method: "POST" });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setImageLoading(false);
    }
  }

  async function saveNarrativeLens() {
    setLoading(true);
    try {
      await api(`/session/${sessionId}/narrative-agent`, {
        method: "PUT",
        body: JSON.stringify({ selected_player_id: selectedNarrativePlayerId }),
      });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function buildNarrative() {
    await saveNarrativeLens();
    setLoading(true);
    setNarrativeBuilding(true);
    try {
      await api(`/session/${sessionId}/build-narrative`, { method: "POST" });
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setNarrativeBuilding(false);
      setLoading(false);
    }
  }

  async function resetChapter() {
    if (!window.confirm("Reset the current MK2 session?")) return;
    setLoading(true);
    try {
      await api(`/session/${sessionId}/reset`, { method: "POST" });
      await refresh();
      setTab(1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function downloadChapter() {
    const chapterText = latestDraft?.chapter_text ?? "";
    const blob = new Blob([chapterText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `chapter-${sessionId || "mk2"}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  if (!catalog || !detail) {
    return <div className="loading-shell">Loading MK2 session...</div>;
  }

  return (
    <div className="page">
      <audio
        ref={audioRef}
        src={MUSIC_TRACKS[trackIndex]}
        onEnded={() => setTrackIndex((current) => (current + 1) % MUSIC_TRACKS.length)}
      />
      {!unlocked && (
        <div className="splash-overlay">
          <article className="splash-card">
            <h1>Welcome to Story Engine MK2</h1>
            <p>
              Story Engine MK2 is an experimental AI-powered tabletop adventure simulator. You act as the Game Master while a
              party of AI-controlled players explores, fights, and roleplays through a dynamic fantasy scenario. The interface is
              organized into three tabs that guide the flow of play.
            </p>
            <p>
              <strong>Tab 1 – Party Setup</strong><br />
              Start here. Choose the players who will make up the party, assign them character classes, and select the mission the
              group will attempt. Each player has a distinct personality and playstyle, so different combinations will produce
              different group dynamics. Once your party and scenario are selected, the adventure is ready to begin.
            </p>
            <p>
              <strong>Tab 2 – Live Adventure</strong><br />
              This is where the game actually happens. Enter prompts to describe situations, environments, or encounters. The AI
              players will react, make decisions, roll dice, and carry the story forward. Combat, exploration, and roleplay all
              take place here. You guide the world as the GM while the agents act as the party.
            </p>
            <p>
              <strong>Tab 3 – Story Chronicle</strong><br />
              When the session reaches a natural stopping point, generate a written narrative of the adventure. You can choose
              which player’s voice will tell the story, giving each chronicle a different tone and perspective. This tab compiles
              the events of the session into a cohesive narrative record.
            </p>
            <p>
              <strong>Quick Start</strong><br />
              1. Configure your party and mission in Tab 1.<br />
              2. Move to Tab 2 and begin the adventure by describing the opening scene.<br />
              3. When the session ends, visit Tab 3 to create the written chronicle.
            </p>
            <p>
              Experiment with different party combinations, missions, and GM prompts. The story engine will respond differently
              each time.
            </p>
            <p><strong>Enter your Testing Password below:</strong></p>
            <form className="splash-form" onSubmit={submitPassword}>
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="Testing password"
              />
              <button className="btn accent" type="submit">Enter</button>
            </form>
            {passwordError && <div className="splash-error">{passwordError}</div>}
          </article>
        </div>
      )}
      <header className="hero">
        <div>
          <div className="eyebrow">Story Engine MK2</div>
          <h1 className="hero-title">Valaska Adventure Console</h1>
          <p className="hero-copy">Preset-driven party setup, GM-first prompt loop, structured memory, initiative scaffolding, and chapter drafting.</p>
        </div>
        <div className="status-strip">
          <div className="status-card"><span>Session</span><strong>{sessionId}</strong></div>
          <div className="status-card"><span>State</span><strong>{detail.session.state}</strong></div>
          <div className="status-card"><span>Round</span><strong>{detail.session.combat_state.in_combat ? detail.session.combat_state.round : "-"}</strong></div>
          <div className="status-card">
            <span>Music</span>
            <strong>{musicPlaying ? "Playing" : "Paused"}</strong>
            <div className="music-controls">
              <button className="btn music-btn" type="button" onClick={() => void toggleMusicPlayback()}>
                {musicPlaying ? "Pause" : "Play"}
              </button>
              <button className="btn music-btn" type="button" onClick={toggleMusicMuted}>
                {musicMuted ? "Unmute" : "Mute"}
              </button>
            </div>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={tab === 1 ? "tab active" : "tab"} onClick={() => setTab(1)}>Tab1</button>
        <button className={tab === 2 ? "tab active" : "tab"} onClick={() => setTab(2)} disabled={!detail.session.tab1_locked}>Tab2</button>
        <button className={tab === 3 ? "tab active" : "tab"} onClick={() => setTab(3)} disabled={!detail.session.tab1_locked}>Tab3</button>
      </nav>

      {error && <div className="error-banner">{error}</div>}

      {tab === 1 && (
        <section className="panel">
          <div className="panel-grid panel-grid--tab1">
            <article className="card map-card">
              <div className="card-head"><span>Cell 1</span><h2>Valaska Map</h2></div>
              <img
                className="media"
                src={resolveApiUrl(adventurePickerOpen ? catalog.adventure_selection_image_url : catalog.map_image_url)}
                alt="Valaska"
              />
              <p className="card-copy">The setting is fixed to Valaska. Moosehearth is the starting town for every MK2 session.</p>
            </article>

            <article className="card" onMouseEnter={() => setAdventurePickerOpen(true)} onMouseLeave={() => setAdventurePickerOpen(false)}>
              <div className="card-head"><span>Cell 2</span><h2>Adventure Selection</h2></div>
              <div className="adventure-list">
                {catalog.adventures.map((adventure) => (
                  <button
                    key={adventure.adventure_id}
                    className={adventureId === adventure.adventure_id ? "adventure-card selected" : "adventure-card"}
                    onClick={() => setAdventureId(adventure.adventure_id)}
                  >
                    <strong>{adventure.title}</strong>
                    <p>{adventure.description}</p>
                  </button>
                ))}
              </div>
            </article>

            <article className="card">
              <div className="card-head"><span>Cell 3</span><h2>Player Picker</h2></div>
              <div className="player-grid">
                {catalog.players.map((player) => {
                  const selected = selectedPlayerIds.includes(player.player_id);
                  return (
                    <button key={player.player_id} className={selected ? "player-tile selected" : "player-tile"} onClick={() => togglePlayer(player.player_id)}>
                      <img src={resolveApiUrl(player.image_url)} alt={player.name} />
                      <strong>{player.name}</strong>
                      <span>{player.keywords.join(" • ")}</span>
                    </button>
                  );
                })}
              </div>
            </article>

            <article className="card">
              <div className="card-head"><span>Cell 4</span><h2>Assign Classes</h2></div>
              <div className="class-grid">
                {selectedPlayerIds.map((playerId, index) => {
                  const player = catalog.players.find((entry) => entry.player_id === playerId)!;
                  const selectedClassId = classByPlayer[playerId] ?? "";
                  const portrait = detail.tab1.party.find((member) => member.player_id === playerId)?.portrait_url ?? player.image_url;
                  return (
                    <div key={playerId} className="class-card">
                      <img src={resolveApiUrl(selectedClassId ? portrait : player.image_url)} alt={player.name} />
                      <div>
                        <strong>{index + 1}. {player.name}</strong>
                        <p>{player.archetype} • {player.race}</p>
                      </div>
                      <select value={selectedClassId} onChange={(e) => setPlayerClass(playerId, e.target.value)}>
                        <option value="">Choose class</option>
                        {catalog.classes.map((classItem) => <option key={classItem.class_id} value={classItem.class_id}>{classItem.name}</option>)}
                      </select>
                    </div>
                  );
                })}
              </div>
            </article>
          </div>

          {selectedAdventure && (
            <div className="summary-bar">
              <strong>{selectedAdventure.title}</strong>
              <span>{selectedAdventure.objectives.map((objective) => objective.description).join(" | ")}</span>
            </div>
          )}

          <div className="action-row">
            <button className="btn" onClick={() => void saveTab1()} disabled={loading}>Save Page</button>
            {!detail.session.tab1_locked && <button className="btn accent" onClick={() => void startChapter()} disabled={loading || !startReady}>Start Chapter</button>}
            {detail.session.tab1_locked && <button className="btn danger" onClick={() => void resetChapter()} disabled={loading}>Reset Chapter</button>}
          </div>
        </section>
      )}

      {tab === 2 && (
        <section className="panel">
          <div className="panel-grid panel-grid--top">
            <article className="card transcript-card">
              <div className="card-head"><span>Cell 1</span><h2>Context Transcript</h2><small>{transcriptChars} chars</small></div>
              <div ref={transcriptRef} className="transcript-box transcript-box--tall">
                {transcript.map((event) => (
                  <div
                    key={event.event_id}
                    className="transcript-line"
                    style={{ color: event.role === "agent" && event.agent_slot ? SLOT_COLORS[event.agent_slot] : "var(--text-primary)" }}
                  >
                    {event.text}
                  </div>
                ))}
              </div>
            </article>

            <article className="card image-card">
              <div className="card-head"><span>Image Cell</span><h2>Scene Frame</h2></div>
              {imageLoading ? (
                <div className="media media-loading">Loading...</div>
              ) : (
                <img className="media" src={resolveApiUrl(detail.image_state.image_url || catalog.default_image_url)} alt="Current scene" />
              )}
              <p className="card-copy">
                {imageLoading ? "Generating a fresh scene image..." : detail.image_state.prompt_text || "Default scene image loaded."}
              </p>
            </article>
          </div>

          <article className="card prompt-shell" style={{ borderColor: SLOT_COLORS[activeAgentSlot] ?? "var(--border-strong)" }}>
            <div className="card-head"><span>Cell 2</span><h2>Prompting</h2></div>
            <div className="agent-tabs">
              {detail.tab1.party.map((member) => (
                <button
                  key={member.slot}
                  className={activeAgentSlot === member.slot ? "agent-chip active" : "agent-chip"}
                  style={{ background: activeAgentSlot === member.slot ? SLOT_COLORS[member.slot] : "transparent", borderColor: SLOT_COLORS[member.slot] }}
                  onClick={() => setActiveAgentSlot(member.slot)}
                >
                  {member.player_name} {member.initiative ? `(${member.initiative})` : ""}
                </button>
              ))}
            </div>
            <form onSubmit={submitPrompt} className="prompt-form">
              <textarea value={userPrompt} onChange={(e) => setUserPrompt(e.target.value)} placeholder="GM prompt..." disabled={detail.session.state !== "ACTIVE"} />
              <div className="action-row">
                <button className="btn" type="submit" disabled={loading || detail.session.state !== "ACTIVE"}>Send Prompt</button>
                <button className="btn accent" type="button" onClick={() => void rollInitiative()} disabled={loading}>Roll for Initiative</button>
                <button className="btn accent" type="button" onClick={() => void generateImage()} disabled={imageLoading}>Generate Image</button>
              </div>
            </form>
          </article>

          <article className="card card-full-width">
              <div className="card-head"><span>Cell 3</span><h2>Player Status</h2></div>
              <div className="status-grid status-grid--row">
                {detail.tab1.party.map((member) => (
                  <div key={member.slot} className="status-card-lg">
                    <img src={resolveApiUrl(member.portrait_url)} alt={member.player_name} />
                    <strong>{member.player_name} the {member.class_id}</strong>
                    <span>AC {member.armor_class} | HP {member.hp_current}/{member.hp_max}</span>
                    <span>{member.status_effects.length ? member.status_effects.join(", ") : "No active status effects"}</span>
                    <p>{member.inventory.join(" • ")}</p>
                  </div>
                ))}
              </div>
              <div className="action-row split-row">
                <button className="btn danger end-button" onClick={() => void endChapter()} disabled={loading || detail.session.state !== "ACTIVE"}>End Chapter</button>
              </div>
          </article>

          <article className="card card-full-width">
              <div className="card-head"><span>Cell 4</span><h2>GM Notes</h2></div>
              <div className="objective-strip">
                <strong>Adventure Completion Objectives</strong>
                <ul className="objective-list">
                  {(detail.tab1.active_adventure?.objectives ?? []).map((objective) => (
                    <li key={objective.id}>{objective.description}</li>
                  ))}
                </ul>
              </div>
              <div className="monster-strip">
                {detail.gm_monsters.map((monster) => (
                  <div key={monster.monster_id} className="monster-card">
                    <strong>{monster.monster_id}</strong>
                    <span>AC {monster.ac} | HP {monster.hp}</span>
                    <span>Atk +{monster.attack_bonus}</span>
                    <p>{monster.attack_text}</p>
                  </div>
                ))}
              </div>
              <div className="dice-box">
                <input value={diceFormula} onChange={(e) => setDiceFormula(e.target.value)} placeholder="1d20+3" />
                <button className="btn" onClick={() => void rollDice()} disabled={loading}>Roll Dice</button>
              </div>
              {diceResult && <p className="dice-result">{diceResult}</p>}
          </article>
        </section>
      )}

      {tab === 3 && (
        <section className="panel">
          <article className="card">
            <div className="card-head"><span>Cell 1</span><h2>Structured Memory</h2></div>
            <pre className="memory-box">{detail.memory_blocks.map((block) => `${block.type} [${block.from_prompt_index}-${block.to_prompt_index}]\n${JSON.stringify(block.json_payload, null, 2)}`).join("\n\n")}</pre>
          </article>

          <article className="card">
            <div className="card-head"><span>Cell 2</span><h2>Who would you like to Summerize your adventure?</h2></div>
            <div className="lens-grid lens-grid--row">
              {detail.tab1.party.map((member) => (
                <button key={member.player_id} className={selectedNarrativePlayerId === member.player_id ? "lens-card lens-card--compact selected" : "lens-card lens-card--compact"} onClick={() => setSelectedNarrativePlayerId(member.player_id)}>
                  <img src={resolveApiUrl(member.portrait_url)} alt={member.player_name} />
                  <strong>{member.player_name}</strong>
                  <span>{member.archetype}</span>
                </button>
              ))}
            </div>
            <div className="action-row">
              <button className="btn accent" onClick={() => void buildNarrative()} disabled={loading || detail.session.state !== "ENDED" || !selectedNarrativePlayerId}>
                {narrativeBuilding ? "Building..." : "Build Narrative"}
              </button>
            </div>
          </article>

          <article className="card">
            <div className="card-head"><span>Cell 3</span><h2>Chapter Draft</h2></div>
            <pre className="memory-box">{latestDraft?.chapter_text ?? ""}</pre>
            <div className="action-row">
              <button className="btn" onClick={downloadChapter} disabled={!(latestDraft?.chapter_text ?? "").trim()}>Download Chapter</button>
            </div>
          </article>
        </section>
      )}
    </div>
  );
}
