// Bet Bot Manager API JavaScript
function renderLiveScores(leagues) {
    const container = document.getElementById('betbot-live-scores');
    if (!container) return;
    
    if (!leagues || leagues.length === 0) {
        container.innerHTML = '<p>No live games available.</p>';
        return;
    }
    
    let html = '';
    leagues.forEach(league => {
        html += `<div class="league-card">
            <h3>${league.league_name}</h3>
            <div class="games">`;
        
        league.games.forEach(game => {
            html += `<div class="game">
                <span>${game.home_team} vs ${game.away_team}</span>
                <span>${game.home_score} - ${game.away_score}</span>
                <span class="status ${game.game_status}">${game.game_status}</span>
            </div>`;
        });
        
        html += `</div></div>`;
    });
    
    container.innerHTML = html;
}

function renderGuildStats(guilds) {
    const container = document.getElementById('betbot-guild-stats');
    if (!container) return;
    
    if (!guilds || guilds.length === 0) {
        container.innerHTML = '<p>No guild data available.</p>';
        return;
    }
    
    let html = '<div class="guilds-grid">';
    guilds.forEach(guild => {
        html += `<div class="guild-card">
            <h3>${guild.guild_name}</h3>
            <div class="stats">
                <div>Monthly: ${guild.monthly_units}</div>
                <div>Yearly: ${guild.yearly_units}</div>
            </div>
        </div>`;
    });
    html += '</div>';
    
    container.innerHTML = html;
}
