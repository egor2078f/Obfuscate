<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Ravion Scripts Hub</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0F0F11; /* Глубокий темный фон */
            --card-bg: #18181B;   /* Немного светлее для карточек */
            --primary: #3B82F6;   /* Спокойный синий акцент */
            --text-main: #FFFFFF;
            --text-sec: #A1A1AA;
            --border: #27272A;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 16px;
            padding-bottom: 80px; /* Место для прокрутки */
        }

        /* --- HEADER --- */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        .header h1 {
            font-size: 22px;
            font-weight: 700;
            background: linear-gradient(90deg, #fff, #ccc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .user-tag {
            background: rgba(59, 130, 246, 0.1);
            color: var(--primary);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        /* --- SEARCH --- */
        .search-container {
            position: sticky;
            top: 0;
            z-index: 10;
            background: var(--bg-color);
            padding-bottom: 16px;
        }

        .search-box {
            position: relative;
            width: 100%;
        }

        .search-input {
            width: 100%;
            padding: 14px 16px 14px 44px;
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: white;
            font-size: 15px;
            transition: border-color 0.2s;
            outline: none;
        }

        .search-input:focus {
            border-color: var(--primary);
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-sec);
        }

        /* --- TABS --- */
        .tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            overflow-x: auto;
            padding-bottom: 4px;
        }

        .tab {
            padding: 8px 16px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 13px;
            color: var(--text-sec);
            white-space: nowrap;
            cursor: pointer;
            transition: 0.2s;
        }

        .tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        /* --- CONTENT GRID --- */
        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text-sec);
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: transform 0.1s, background-color 0.2s;
            cursor: pointer;
        }

        .card:active {
            transform: scale(0.98);
            background-color: #202024;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
        }

        .game-title {
            font-weight: 600;
            font-size: 16px;
            color: #fff;
        }

        .views-badge {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            color: var(--text-sec);
            background: #27272a;
            padding: 2px 6px;
            border-radius: 6px;
        }

        .card-desc {
            font-size: 13px;
            color: var(--text-sec);
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .card-footer {
            margin-top: 8px;
            display: flex;
            gap: 8px;
        }

        .tag {
            font-size: 10px;
            padding: 4px 8px;
            border-radius: 4px;
            background: #27272A;
            color: #A1A1AA;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .tag.key-req { color: #F87171; background: rgba(248, 113, 113, 0.1); }
        .tag.no-key { color: #4ADE80; background: rgba(74, 222, 128, 0.1); }

        /* --- SKELETON LOADING ANIMATION --- */
        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }
        .loading { animation: pulse 1.5s infinite; }

    </style>
</head>
<body>

    <div class="header">
        <h1>Ravion Scripts</h1>
        <div class="user-tag" id="user-name">Guest</div>
    </div>

    <div class="search-container">
        <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" class="search-input" placeholder="Найти игру или скрипт..." id="search-input">
        </div>
    </div>

    <div class="tabs">
        <div class="tab active" onclick="filter('all', this)">🔥 Топ</div>
        <div class="tab" onclick="filter('new', this)">🆕 Новые</div>
        <div class="tab" onclick="filter('mobile', this)">📱 Mobile</div>
    </div>

    <div class="section-title">Результаты</div>
    <div class="grid" id="scripts-grid">
        </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand(); // Раскрыть на весь экран
        
        // Настройка цветов под тему Telegram (если нужно, можно убрать и оставить темную)
        // tg.setHeaderColor('#0F0F11'); 
        // tg.setBackgroundColor('#0F0F11');

        const userNameEl = document.getElementById('user-name');
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userNameEl.textContent = tg.initDataUnsafe.user.first_name;
        }

        // --- MOCK DATA (Имитация данных из твоей БД) ---
        // В реальном WebApp ты будешь делать fetch запрос к своему API
        const mockScripts = [
            { id: 'uuid1', title: 'Blox Fruits Auto Farm', views: 1250, desc: 'Лучший автофарм, авторейд, телепорты. Работает на мобилках.', key: false, tags: ['Mobile', 'OP'] },
            { id: 'uuid2', title: 'Pet Simulator 99', views: 890, desc: 'Автооткрытие яиц, снайпер на аукционе, гем фарм.', key: true, tags: ['PC', 'Huge'] },
            { id: 'uuid3', title: 'Doors Entity Spawner', views: 540, desc: 'Спавн любых сущностей, годмод, проход сквозь стены.', key: false, tags: ['Fun', 'Troll'] },
            { id: 'uuid4', title: 'Blade Ball Kill Aura', views: 2100, desc: 'Автоматическое отбивание мяча, визуалы.', key: false, tags: ['PvP', 'Hot'] },
            { id: 'uuid5', title: 'Da Hood Aimlock', views: 110, desc: 'Жесткий аимлок, сайлент аим, флай.', key: true, tags: ['PvP'] },
        ];

        const grid = document.getElementById('scripts-grid');

        function renderCards(data) {
            grid.innerHTML = '';
            data.forEach(script => {
                const card = document.createElement('div');
                card.className = 'card';
                card.onclick = () => selectScript(script.id);

                const keyTag = script.key 
                    ? `<span class="tag key-req">🔐 Key</span>` 
                    : `<span class="tag no-key">🔓 No Key</span>`;

                card.innerHTML = `
                    <div class="card-header">
                        <div class="game-title">${script.title}</div>
                        <div class="views-badge">👀 ${script.views}</div>
                    </div>
                    <div class="card-desc">${script.desc}</div>
                    <div class="card-footer">
                        ${keyTag}
                        ${script.tags.map(t => `<span class="tag">#${t}</span>`).join('')}
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        // Инициализация
        renderCards(mockScripts);

        // Поиск
        document.getElementById('search-input').addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            const filtered = mockScripts.filter(s => 
                s.title.toLowerCase().includes(val) || 
                s.desc.toLowerCase().includes(val)
            );
            renderCards(filtered);
        });

        // Переключение табов (визуальное)
        window.filter = (type, el) => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            el.classList.add('active');
            // Здесь можно добавить логику сортировки
            renderCards(mockScripts); // Пока просто сброс
        };

        // ОТПРАВКА ДАННЫХ ОБРАТНО В БОТА
        function selectScript(uuid) {
            // Отправляем данные в бота
            tg.sendData(uuid);
            // Или закрываем (бота нужно научить принимать данные)
        }

    </script>
</body>
</html>
