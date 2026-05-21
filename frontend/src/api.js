const API_BASE = import.meta.env.VITE_API_BASE || \'http://localhost:8000\';

const defaultHeaders = {
  \'Content-Type\': \'application/json\',
  \'X-Requested-With\': \'XMLHttpRequest\',
};

// --- Search API ---
export async function searchMedia(query, mediaType = \'anime\') {
  const res = await fetch(\\/fr/api/search/?q=\&media_type=\\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Search failed: \\);
  return res.json();
}

// --- Classic Game API ---
export async function startClassicGame(mediaType = \'anime\', difficulty = \'normal\') {
  const res = await fetch(\\/fr/api/v1/game/classic/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ media_type: mediaType, difficulty }),
  });
  if (!res.ok) throw new Error(\Start game failed: \\);
  return res.json();
}

export async function getClassicGameState(sessionId) {
  const res = await fetch(\\/fr/api/v1/game/classic/state/?session_id=\\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get state failed: \\);
  return res.json();
}

export async function guessClassicGame(sessionId, guess, mediaType = \'anime\') {
  const res = await fetch(\\/fr/api/v1/game/classic/guess/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ session_id: sessionId, guess, media_type: mediaType }),
  });
  if (!res.ok) throw new Error(\Guess failed: \\);
  return res.json();
}

export async function revealClassicGame(sessionId) {
  const res = await fetch(\\/fr/api/v1/game/classic/reveal/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error(\Reveal failed: \\);
  return res.json();
}

// --- Emoji Decode Game API ---
export async function startEmojiGame(mediaType = \'Anime\') {
  const res = await fetch(\\/fr/api/v1/game/emoji/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ media_type: mediaType }),
  });
  if (!res.ok) throw new Error(\Start emoji game failed: \\);
  return res.json();
}

export async function getEmojiGameState() {
  const res = await fetch(\\/fr/api/v1/game/emoji/state/\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get emoji state failed: \\);
  return res.json();
}

export async function guessEmojiGame(guess) {
  const res = await fetch(\\/fr/api/v1/game/emoji/guess/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ guess }),
  });
  if (!res.ok) throw new Error(\Emoji guess failed: \\);
  return res.json();
}

// --- Akinetix Game API ---
export async function startAkinetixGame(mediaType = \'Anime\') {
  const res = await fetch(\\/fr/api/v1/game/akinetix/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ media_type: mediaType }),
  });
  if (!res.ok) throw new Error(\Start akinetix game failed: \\);
  return res.json();
}

export async function getAkinetixGameState() {
  const res = await fetch(\\/fr/api/v1/game/akinetix/state/\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get akinetix state failed: \\);
  return res.json();
}

export async function answerAkinetixGame(answer) {
  const res = await fetch(\\/fr/api/v1/game/akinetix/answer/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ answer }),
  });
  if (!res.ok) throw new Error(\Akinetix answer failed: \\);
  return res.json();
}

export async function confirmAkinetixGame(correct) {
  const res = await fetch(\\/fr/api/v1/game/akinetix/confirm/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ correct }),
  });
  if (!res.ok) throw new Error(\Akinetix confirm failed: \\);
  return res.json();
}

// --- Paradox Game API ---
export async function startParadoxGame(mediaType = \'Anime\') {
  const res = await fetch(\\/fr/api/v1/game/paradox/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ media_type: mediaType }),
  });
  if (!res.ok) throw new Error(\Start paradox game failed: \\);
  return res.json();
}

export async function getParadoxGameState() {
  const res = await fetch(\\/fr/api/v1/game/paradox/state/\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get paradox state failed: \\);
  return res.json();
}

export async function guessParadoxGame(guess) {
  const res = await fetch(\\/fr/api/v1/game/paradox/guess/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ guess }),
  });
  if (!res.ok) throw new Error(\Paradox guess failed: \\);
  return res.json();
}

// --- Vision Quest API ---
export async function startVisionGame(mediaType = \'Anime\', isDaily = false) {
  const res = await fetch(\\/fr/api/v1/game/vision/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ media_type: mediaType, is_daily: isDaily }),
  });
  if (!res.ok) throw new Error(\Start vision game failed: \\);
  return res.json();
}

export async function getVisionGameState() {
  const res = await fetch(\\/fr/api/v1/game/vision/state/\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get vision state failed: \\);
  return res.json();
}

export async function guessVisionGame(description) {
  const res = await fetch(\\/fr/api/v1/game/vision/guess/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ description }),
  });
  if (!res.ok) throw new Error(\Vision guess failed: \\);
  return res.json();
}

// --- Blindtest API ---
export async function startBlindtestGame(themeType = \'Random\', isDaily = false) {
  const res = await fetch(\\/fr/api/v1/game/blindtest/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ type: themeType, is_daily: isDaily }),
  });
  if (!res.ok) throw new Error(\Start blindtest game failed: \\);
  return res.json();
}

export async function getBlindtestGameState() {
  const res = await fetch(\\/fr/api/v1/game/blindtest/state/\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get blindtest state failed: \\);
  return res.json();
}

export async function guessBlindtestGame(guess) {
  const res = await fetch(\\/fr/api/v1/game/blindtest/guess/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ guess }),
  });
  if (!res.ok) throw new Error(\Blindtest guess failed: \\);
  return res.json();
}

// --- Covertest API ---
export async function startCovertestGame(isDaily = false) {
  const res = await fetch(\\/fr/api/v1/game/covertest/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ is_daily: isDaily }),
  });
  if (!res.ok) throw new Error(\Start covertest game failed: \\);
  return res.json();
}

export async function getCovertestGameState() {
  const res = await fetch(\\/fr/api/v1/game/covertest/state/\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get covertest state failed: \\);
  return res.json();
}

export async function guessCovertestGame(guess) {
  const res = await fetch(\\/fr/api/v1/game/covertest/guess/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ guess }),
  });
  if (!res.ok) throw new Error(\Covertest guess failed: \\);
  return res.json();
}

// --- Archetypist API ---
export async function startArchetypistFusion(data) {
  const res = await fetch(\\/fr/api/v1/game/archetypist/start/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(\Start archetypist failed: \\);
  return res.json();
}

export async function getArchetypistStatus(taskId, fusionId) {
  const res = await fetch(\\/fr/api/v1/game/archetypist/status/?task_id=\&fusion_id=\\, {
    headers: defaultHeaders,
    credentials: \'include\',
  });
  if (!res.ok) throw new Error(\Get archetypist status failed: \\);
  return res.json();
}

export async function likeArchetypistFusion(fusionId) {
  const res = await fetch(\\/fr/api/v1/game/archetypist/like/\, {
    method: \'POST\',
    headers: defaultHeaders,
    credentials: \'include\',
    body: JSON.stringify({ fusion_id: fusionId }),
  });
  if (!res.ok) throw new Error(\Like archetypist failed: \\);
  return res.json();
}
