/**
 * Moteur de Jeu Offline Pro pour Animetix
 * Utilise SQLite WASM (sql.js) pour des recherches complexes et massives.
 */

class OfflineEngine {
    constructor() {
        this.db = null;
        this.isLoaded = false;
        this.secretItem = null;
        this.mediaType = 'Anime';
        this.guesses = [];
        this.SQL = null;
    }

    async init() {
        if (this.isLoaded) return;
        try {
            // 1. Charger WebAssembly sql.js
            const config = {
                locateFile: filename => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.12.0/${filename}`
            };
            this.SQL = await initSqlJs(config);

            // 2. Récupérer la base binaire
            const response = await fetch('/static/animetix/data/offline_catalog.db');
            const arrayBuffer = await response.arrayBuffer();
            
            // 3. Ouvrir la base
            this.db = new this.SQL.Database(new Uint8Array(arrayBuffer));
            this.isLoaded = true;
            console.log("💎 Animetix SQLite Offline Engine Active.");
        } catch (error) {
            console.error("❌ Failed to initialize SQLite WASM:", error);
        }
    }

    startNewGame(mediaType = 'Anime') {
        if (!this.isLoaded) return;
        this.mediaType = mediaType;
        this.guesses = [];

        // Sélection d'un secret aléatoire via SQL
        const res = this.db.exec(`SELECT * FROM media WHERE type = '${mediaType}' ORDER BY RANDOM() LIMIT 1`);
        if (res.length > 0) {
            const columns = res[0].columns;
            const values = res[0].values[0];
            this.secretItem = columns.reduce((obj, col, i) => ({...obj, [col]: values[i]}), {});
            
            // Récupération des tags du secret
            const tagsRes = this.db.exec(`SELECT name FROM tags WHERE media_id = '${this.secretItem.id}'`);
            this.secretItem.all_tags = tagsRes.length > 0 ? tagsRes[0].values.map(v => v[0]) : [];
            
            console.log(`🎮 Offline Game Started. Target ID: ${this.secretItem.id}`);
            return this.secretItem;
        }
    }

    calculateSimilarity(guessTitle) {
        if (guessTitle === this.secretItem.title) return 100;

        // 1. Récupérer l'item deviné
        const res = this.db.exec(`SELECT id FROM media WHERE title = ? LIMIT 1`, [guessTitle]);
        if (res.length === 0) return 0;
        const guessId = res[0].values[0][0];

        // 2. Récupérer ses tags
        const tagsRes = this.db.exec(`SELECT name FROM tags WHERE media_id = ?`, [guessId]);
        const guessTags = tagsRes.length > 0 ? tagsRes[0].values.map(v => v[0]) : [];

        // 3. Jaccard Similarity (Inter / Union)
        const secretSet = new Set(this.secretItem.all_tags);
        const guessSet = new Set(guessTags);
        
        const intersection = [...secretSet].filter(x => guessSet.has(x)).length;
        const union = new Set([...secretSet, ...guessSet]).size;
        
        if (union === 0) return 0;
        const score = (intersection / union) * 100;
        return Math.min(99.9, Math.round(score * 100) / 100);
    }

    makeGuess(guessTitle) {
        // Recherche de l'item complet pour l'UI
        const res = this.db.exec(`SELECT * FROM media WHERE title = ? LIMIT 1`, [guessTitle]);
        let item = null;
        if (res.length > 0) {
            const columns = res[0].columns;
            const values = res[0].values[0];
            item = columns.reduce((obj, col, i) => ({...obj, [col]: values[i]}), {});
        }

        const score = this.calculateSimilarity(guessTitle);
        
        const guess = {
            title: guessTitle,
            title_english: item?.title_en,
            title_native: item?.title_jp,
            image: item?.image,
            score: score,
            color: score > 90 ? "danger" : score > 70 ? "warning" : score > 40 ? "primary" : "secondary"
        };

        this.guesses.push(guess);
        this.guesses.sort((a, b) => b.score - a.score);
        
        if (score === 100) {
            this.saveOfflineWin();
        }

        return {
            guesses: this.guesses,
            isCorrect: score === 100
        };
    }

    saveOfflineWin() {
        const winData = {
            score: 100,
            game_mode: 'classic',
            media_type: this.mediaType,
            attempts: this.guesses.length,
            timestamp: Date.now()
        };
        
        const offlineScores = JSON.parse(localStorage.getItem('offlineScores') || '[]');
        offlineScores.push(winData);
        localStorage.setItem('offlineScores', JSON.stringify(offlineScores));
        console.log("💾 Offline win saved locally.");

        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then(swRegistration => {
                return swRegistration.sync.register('sync-offline-scores');
            }).catch(err => {
                console.error("Background Sync could not be registered:", err);
            });
        }
    }

    // Méthode bonus : Recherche complexe offline
    search(query, limit = 5) {
        const res = this.db.exec(`
            SELECT title, image FROM media 
            WHERE (title LIKE ? OR title_en LIKE ?) AND type = ?
            LIMIT ?
        `, [`%${query}%`, `%${query}%`, this.mediaType, limit]);
        
        if (res.length === 0) return [];
        return res[0].values.map(v => ({ title: v[0], image: v[1] }));
    }
}

window.offlineEngine = new OfflineEngine();
