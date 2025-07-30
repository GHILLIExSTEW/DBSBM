<?php
/*
Template Name: Live Scores
*/

get_header(); ?>

<div class="live-scores-container">
    <div class="hero-section">
        <h1 class="hero-title">
            <i class="fas fa-trophy"></i>
            <?php the_title(); ?>
        </h1>
        <p class="hero-subtitle">Real-time sports scores and updates</p>
    </div>

    <div id="live-scores-widget">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading live scores...</p>
        </div>
    </div>
</div>

<style>
.live-scores-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.hero-section {
    text-align: center;
    margin-bottom: 40px;
}

.hero-title {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 10px;
}

.hero-subtitle {
    font-size: 1.2rem;
    color: #666;
}

.loading {
    text-align: center;
    padding: 40px;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* League Cards */
.league-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.league-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.league-logo {
    width: 40px;
    height: 40px;
    margin-right: 15px;
    border-radius: 50%;
}

.league-name {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin: 0;
}

.league-name a {
    color: inherit;
    text-decoration: none;
}

.league-name a:hover {
    color: #3498db;
}

.games-container {
    display: grid;
    gap: 10px;
}

.game-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.game-teams {
    flex: 1;
}

.game-score {
    font-weight: bold;
    font-size: 1.2rem;
    color: #333;
}

.game-status {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
}

.status-live {
    background: #e74c3c;
    color: white;
}

.status-halftime {
    background: #f39c12;
    color: white;
}

.status-scheduled {
    background: #3498db;
    color: white;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #666;
}

.empty-state i {
    font-size: 3rem;
    margin-bottom: 20px;
    color: #ccc;
}
</style>

<script>
// API configuration
const API_BASE_URL = '<?php echo get_option("betbot_api_url", "http://app.yourdomain.com"); ?>';

// Fetch and render live scores
async function loadLiveScores() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/live-scores`);
        const data = await response.json();
        
        if (data.success) {
            renderLiveScores(data.leagues);
        } else {
            showError('Failed to load live scores');
        }
    } catch (error) {
        console.error('Error loading live scores:', error);
        showError('Error loading live scores');
    }
}

function renderLiveScores(leagues) {
    const container = document.getElementById('live-scores-widget');
    
    if (!leagues || leagues.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clock"></i>
                <h3>No Live Games</h3>
                <p>There are currently no live games. Check back later!</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    leagues.forEach(league => {
        html += `
            <div class="league-card">
                <div class="league-header">
                    ${league.league_logo ? `<img src="${league.league_logo}" alt="${league.league_name}" class="league-logo">` : ''}
                    <h3 class="league-name">
                        <a href="/league/${league.league_id}">${league.league_name}</a>
                    </h3>
                </div>
                <div class="games-container">
        `;
        
        if (league.games && league.games.length > 0) {
            league.games.forEach(game => {
                const statusClass = `status-${game.game_status}`;
                html += `
                    <div class="game-card">
                        <div class="game-teams">
                            <div>${game.home_team} vs ${game.away_team}</div>
                            <small>${formatGameTime(game.game_time)}</small>
                        </div>
                        <div class="game-score">
                            ${game.home_score} - ${game.away_score}
                        </div>
                        <div class="game-status ${statusClass}">
                            ${game.game_status.toUpperCase()}
                        </div>
                    </div>
                `;
            });
        } else {
            html += `
                <div class="empty-state">
                    <p>No games scheduled for this league</p>
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function formatGameTime(timeString) {
    if (!timeString) return '';
    const date = new Date(timeString);
    return date.toLocaleString();
}

function showError(message) {
    const container = document.getElementById('live-scores-widget');
    container.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadLiveScores();
    
    // Auto-refresh every 30 seconds
    setInterval(loadLiveScores, 30000);
});
</script>

<?php get_footer(); ?>
