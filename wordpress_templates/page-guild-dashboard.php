<?php
/*
Template Name: Guild Dashboard
*/

get_header(); ?>

<div class="guild-dashboard">
    <div class="hero-section">
        <h1 class="hero-title">
            <i class="fas fa-users"></i>
            Guild Dashboard
        </h1>
        <p class="hero-subtitle">Track your guild performance and statistics</p>
    </div>

    <div id="guilds-widget">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading guild data...</p>
        </div>
    </div>
</div>

<style>
.guild-dashboard {
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

/* Guild Cards */
.guilds-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.guild-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.guild-card:hover {
    transform: translateY(-5px);
}

.guild-name {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin-bottom: 15px;
}

.guild-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-bottom: 15px;
}

.stat-item {
    text-align: center;
}

.stat-label {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 5px;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
}

.stat-positive {
    color: #27ae60;
}

.stat-negative {
    color: #e74c3c;
}

.guild-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.btn {
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    transition: all 0.3s ease;
}

.btn-primary {
    background: #3498db;
    color: white;
}

.btn-primary:hover {
    background: #2980b9;
}

.btn-secondary {
    background: #95a5a6;
    color: white;
}

.btn-secondary:hover {
    background: #7f8c8d;
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

// Fetch and render guilds
async function loadGuilds() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/guilds`);
        const data = await response.json();
        
        if (data.success) {
            renderGuilds(data.guilds);
        } else {
            showError('Failed to load guild data');
        }
    } catch (error) {
        console.error('Error loading guilds:', error);
        showError('Error loading guild data');
    }
}

function renderGuilds(guilds) {
    const container = document.getElementById('guilds-widget');
    
    if (!guilds || guilds.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <h3>No Active Guilds</h3>
                <p>No active guilds found. Create a guild to get started!</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="guilds-grid">';
    
    guilds.forEach(guild => {
        const monthlyClass = guild.monthly_units >= 0 ? 'stat-positive' : 'stat-negative';
        const yearlyClass = guild.yearly_units >= 0 ? 'stat-positive' : 'stat-negative';
        
        html += `
            <div class="guild-card">
                <h3 class="guild-name">${guild.guild_name}</h3>
                <div class="guild-stats">
                    <div class="stat-item">
                        <div class="stat-label">Monthly Units</div>
                        <div class="stat-value ${monthlyClass}">
                            ${guild.monthly_units >= 0 ? '+' : ''}${guild.monthly_units}
                        </div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Yearly Units</div>
                        <div class="stat-value ${yearlyClass}">
                            ${guild.yearly_units >= 0 ? '+' : ''}${guild.yearly_units}
                        </div>
                    </div>
                </div>
                <div class="guild-actions">
                    <a href="/guild/${guild.guild_id}" class="btn btn-primary">View Details</a>
                    <a href="/guild/${guild.guild_id}/live-scores" class="btn btn-secondary">Live Scores</a>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function showError(message) {
    const container = document.getElementById('guilds-widget');
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
    loadGuilds();
    
    // Auto-refresh every 60 seconds
    setInterval(loadGuilds, 60000);
});
</script>

<?php get_footer(); ?>
