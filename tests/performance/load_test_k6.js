import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';

// Configurations de base pour le test de charge
export const options = {
  stages: [
    { duration: '20s', target: 10 }, // Montée en charge progressive à 10 utilisateurs virtuels
    { duration: '30s', target: 25 }, // Pic de charge à 25 utilisateurs
    { duration: '10s', target: 0 },  // Descente progressive
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% des requêtes HTTP doivent répondre en moins de 500ms
    http_req_failed: ['rate<0.01'],    // Moins de 1% d'échecs HTTP admis
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8000';

export default function () {
  // --- ÉTAPE 1: Recherche & Autocomplétion ---
  const searchQueries = ['Naruto', 'One Piece', 'Attack on Titan', 'Death Note', 'Bleach'];
  const randomQuery = searchQueries[Math.floor(Math.random() * searchQueries.length)];
  
  const searchRes = http.get(`${BASE_URL}/api/v1/search/?q=${randomQuery}`);
  check(searchRes, {
    'Search status is 200': (r) => r.status === 200,
    'Search has results': (r) => r.json() && r.json().results && r.json().results.length > 0,
  });
  sleep(1);

  // --- ÉTAPE 2: Pipeline RAG / Advanced Search ---
  const ragPayload = JSON.stringify({
    query: `Quels sont les thèmes principaux de ${randomQuery} ?`,
    media_type: 'anime'
  });
  
  const ragParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const ragRes = http.post(`${BASE_URL}/api/v1/search/rag/`, ragPayload, ragParams);
  check(ragRes, {
    'RAG status is 200': (r) => r.status === 200,
    'RAG returns answer': (r) => r.json() && r.json().answer !== undefined,
  });
  sleep(2);

  // --- ÉTAPE 3: Game Classic Endpoints ---
  // Démarrer une session de jeu classic
  const startPayload = JSON.stringify({
    media_type: 'anime',
    difficulty: 'normal'
  });

  const startRes = http.post(`${BASE_URL}/api/v1/game/classic/start/`, startPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  const startSuccess = check(startRes, {
    'Start classic game is 200': (r) => r.status === 200,
    'Session ID is provided': (r) => r.json() && r.json().session_id !== undefined,
  });

  if (startSuccess) {
    const session_id = startRes.json().session_id;

    // Faire une tentative (guess)
    const guessPayload = JSON.stringify({
      session_id: session_id,
      guess: 'Naruto'
    });

    const guessRes = http.post(`${BASE_URL}/api/v1/game/classic/guess/`, guessPayload, {
      headers: { 'Content-Type': 'application/json' },
    });

    check(guessRes, {
      'Guess classic game returns state': (r) => r.status === 200 && r.json().attempts !== undefined,
    });
    sleep(1);
  }

  // --- ÉTAPE 4: Temps réel / WebSocket (Salle de duel Undercover) ---
  const room_id = 'test_perf_room';
  const wsUrl = `${WS_URL}/ws/game/undercover/${room_id}/`;

  ws.connect(wsUrl, {}, function (socket) {
    socket.on('open', () => {
      // Rejoindre le salon
      socket.send(JSON.stringify({
        action: 'join',
        username: `perf_user_${__VU}`,
      }));
      
      // Simuler l'envoi d'un message/indice après 500ms
      socket.setTimeout(() => {
        socket.send(JSON.stringify({
          action: 'send_clue',
          clue: 'Héros courageux',
        }));
      }, 500);

      // Fermer la connexion WebSocket proprement après 2 secondes
      socket.setTimeout(() => {
        socket.close();
      }, 2000);
    });

    socket.on('message', (message) => {
      const msg = JSON.parse(message);
      check(msg, {
        'WS received valid event': (m) => m.type !== undefined,
      });
    });

    socket.on('close', () => {
      // WS déconnecté proprement
    });

    socket.on('error', (err) => {
      check(err, {
        'WS error occurred': () => false,
      });
    });
  });

  sleep(1);
}
