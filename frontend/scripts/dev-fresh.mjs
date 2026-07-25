// Redémarrage propre du serveur Vite : libère le port 5173 (tue une instance
// figée) puis relance Vite. Contourne la désync HMR de Tailwind v4 où les
// utilitaires cessent d'être générés après des éditions rapides de la config —
// un démarrage à froid refait un scan de contenu complet.
//
// Usage : npm run dev:fresh
import { execFileSync, spawn } from 'node:child_process';

const PORT = 5173;

// Exécute un binaire sans shell (pas d'interpolation → pas d'injection).
function run(cmd, args) {
  return execFileSync(cmd, args, { encoding: 'utf8' });
}

function pidsOnPort(port) {
  const pids = new Set();
  try {
    if (process.platform === 'win32') {
      for (const line of run('netstat', ['-ano']).split('\n')) {
        if (line.includes(`:${port} `) && /LISTENING/i.test(line)) {
          const pid = line.trim().split(/\s+/).pop();
          if (/^\d+$/.test(pid) && pid !== '0') pids.add(pid);
        }
      }
    } else {
      for (const pid of run('lsof', ['-ti', `tcp:${port}`]).split('\n')) {
        if (/^\d+$/.test(pid.trim())) pids.add(pid.trim());
      }
    }
  } catch {
    // netstat/lsof a échoué ou rien n'écoute : on renvoie l'ensemble vide.
  }
  return [...pids];
}

const pids = pidsOnPort(PORT);
for (const pid of pids) {
  try {
    if (process.platform === 'win32') run('taskkill', ['/F', '/PID', pid]);
    else run('kill', ['-9', pid]);
  } catch {
    // le process a peut-être déjà disparu — on continue.
  }
}
if (pids.length) console.log(`✓ Port ${PORT} libéré (PID ${pids.join(', ')})`);

// Commande en chaîne statique unique + shell : Windows exige un shell pour lancer
// npx (.cmd) ; sans tableau d'arguments il n'y a ni DEP0190 ni interpolation.
const vite = spawn('npx vite', { stdio: 'inherit', shell: true });
vite.on('exit', (code) => process.exit(code ?? 0));
