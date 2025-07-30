<?php
/*
Plugin Name: Bet Bot Manager Integration
Description: Integrates Flask web portal with WordPress
Version: 1.0
Author: Your Name
*/

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Add admin menu
function betbot_admin_menu() {
    add_options_page(
        'Bet Bot Manager Settings',
        'Bet Bot Manager',
        'manage_options',
        'betbot-settings',
        'betbot_settings_page'
    );
}
add_action('admin_menu', 'betbot_admin_menu');

// Settings page
function betbot_settings_page() {
    if (isset($_POST['submit'])) {
        update_option('betbot_api_url', sanitize_text_field($_POST['api_url']));
        echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
    }
    
    $api_url = get_option('betbot_api_url', 'http://app.yourdomain.com');
    ?>
    <div class="wrap">
        <h1>Bet Bot Manager Settings</h1>
        <form method="post">
            <table class="form-table">
                <tr>
                    <th scope="row">API URL</th>
                    <td>
                        <input type="url" name="api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
                        <p class="description">The URL of your Flask API (e.g., http://app.yourdomain.com)</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}

// Add shortcodes
add_shortcode('live_scores', 'betbot_live_scores_shortcode');
add_shortcode('guild_stats', 'betbot_guild_stats_shortcode');

function betbot_live_scores_shortcode($atts) {
    $api_url = get_option('betbot_api_url', 'http://app.yourdomain.com');
    
    ob_start();
    ?>
    <div id="betbot-live-scores">
        <div class="loading">Loading live scores...</div>
    </div>
    
    <script>
    // Live scores shortcode JavaScript
    fetch('<?php echo esc_url($api_url); ?>/api/live-scores')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Render live scores
                renderLiveScores(data.leagues);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    </script>
    <?php
    return ob_get_clean();
}

function betbot_guild_stats_shortcode($atts) {
    $api_url = get_option('betbot_api_url', 'http://app.yourdomain.com');
    
    ob_start();
    ?>
    <div id="betbot-guild-stats">
        <div class="loading">Loading guild statistics...</div>
    </div>
    
    <script>
    // Guild stats shortcode JavaScript
    fetch('<?php echo esc_url($api_url); ?>/api/guilds')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Render guild stats
                renderGuildStats(data.guilds);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    </script>
    <?php
    return ob_get_clean();
}

// Enqueue scripts and styles
function betbot_enqueue_scripts() {
    wp_enqueue_script('betbot-api', plugin_dir_url(__FILE__) . 'js/betbot-api.js', array(), '1.0', true);
    wp_enqueue_style('betbot-styles', plugin_dir_url(__FILE__) . 'css/betbot-styles.css', array(), '1.0');
}
add_action('wp_enqueue_scripts', 'betbot_enqueue_scripts');
