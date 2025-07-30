# WordPress Integration Guide for Bet Bot Manager

## Overview
This guide explains how to integrate your Flask web portal with WordPress on Bluehost.

## Option 1: WordPress Frontend + Flask API Backend (Recommended)

### Step 1: Set Up WordPress on Bluehost
1. Install WordPress through Bluehost cPanel
2. Choose a theme that supports custom pages
3. Install necessary plugins:
   - **Advanced Custom Fields** (for custom data)
   - **Custom Post Types UI** (for guild pages)
   - **WP REST API** (for API integration)

### Step 2: Configure Flask as API Backend
Create a new Flask API that serves JSON data:

```python
# api_endpoints.py
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow WordPress to access the API

@app.route('/api/guilds')
def get_guilds():
    # Your existing get_active_guilds() logic
    return jsonify(guilds_data)

@app.route('/api/live-scores')
def get_live_scores():
    # Your existing get_live_games() logic
    return jsonify(scores_data)

@app.route('/api/guild/<int:guild_id>')
def get_guild_details(guild_id):
    # Guild-specific data
    return jsonify(guild_data)
```

### Step 3: Create WordPress Custom Pages
1. **Create Custom Post Type for Guilds:**
   ```php
   // functions.php
   function create_guild_post_type() {
       register_post_type('guild',
           array(
               'labels' => array(
                   'name' => 'Guilds',
                   'singular_name' => 'Guild'
               ),
               'public' => true,
               'has_archive' => true,
               'supports' => array('title', 'editor', 'thumbnail')
           )
       );
   }
   add_action('init', 'create_guild_post_type');
   ```

2. **Create Custom Page Templates:**
   - `page-live-scores.php`
   - `page-guild-dashboard.php`
   - `page-player-stats.php`

### Step 4: WordPress Page Template Example
```php
<?php
/*
Template Name: Live Scores
*/

get_header(); ?>

<div class="live-scores-container">
    <h1><?php the_title(); ?></h1>
    
    <div id="live-scores-widget">
        <div class="loading">Loading live scores...</div>
    </div>
</div>

<script>
// Fetch data from Flask API
fetch('/api/live-scores')
    .then(response => response.json())
    .then(data => {
        // Render the data using your existing HTML structure
        renderLiveScores(data);
    });
</script>

<?php get_footer(); ?>
```

## Option 2: WordPress Plugin Approach

### Create a Custom WordPress Plugin
```php
<?php
/*
Plugin Name: Bet Bot Manager Integration
Description: Integrates Flask web portal with WordPress
Version: 1.0
*/

// Add shortcodes for embedding content
add_shortcode('live_scores', 'render_live_scores_shortcode');
add_shortcode('guild_stats', 'render_guild_stats_shortcode');

function render_live_scores_shortcode($atts) {
    $api_url = get_option('betbot_api_url', 'http://your-domain.com/api');
    
    // Fetch data from Flask API
    $response = wp_remote_get($api_url . '/live-scores');
    $data = json_decode(wp_remote_retrieve_body($response), true);
    
    // Return HTML using your existing template structure
    ob_start();
    include(plugin_dir_path(__FILE__) . 'templates/live-scores.php');
    return ob_get_clean();
}
```

## Option 3: Subdomain Approach

### Separate Flask App on Subdomain
1. **Main WordPress Site:** `yourdomain.com`
2. **Flask App:** `app.yourdomain.com`

### Configuration
```apache
# .htaccess for main domain (WordPress)
RewriteEngine On
RewriteBase /

# Flask app on subdomain
RewriteCond %{HTTP_HOST} ^app\.yourdomain\.com$ [NC]
RewriteRule ^(.*)$ /cgi-bin/webapp.py/$1 [L]
```

## Option 4: WordPress Theme Customization

### Create a Custom Theme
1. **Copy your existing HTML templates** to WordPress theme structure
2. **Convert Jinja2 syntax** to PHP
3. **Use WordPress functions** for dynamic content

### Template Conversion Example
```php
<?php
// Convert from Jinja2: {{ leagues }}
// To PHP: <?php foreach($leagues as $league): ?>

<div class="league-card">
    <div class="league-header">
        <?php if($league['logo']): ?>
            <img src="<?php echo esc_url($league['logo']); ?>" alt="<?php echo esc_attr($league['name']); ?>" class="league-logo">
        <?php endif; ?>
        <h3 class="league-name">
            <a href="<?php echo get_permalink($league['page_id']); ?>">
                <?php echo esc_html($league['name']); ?>
            </a>
        </h3>
    </div>
</div>

<?php endforeach; ?>
```

## Recommended Approach: Option 1 (WordPress + Flask API)

### Benefits:
- ✅ WordPress for content management
- ✅ Flask for data processing and API
- ✅ Best of both worlds
- ✅ Easy to maintain
- ✅ SEO-friendly with WordPress

### Implementation Steps:

1. **Deploy Flask API** to Bluehost subdomain or separate directory
2. **Set up WordPress** on main domain
3. **Create custom page templates** in WordPress
4. **Use JavaScript** to fetch data from Flask API
5. **Style with your existing CSS**

### File Structure:
```
public_html/                    # WordPress
├── wp-content/
│   └── themes/
│       └── your-theme/
│           ├── page-live-scores.php
│           └── page-guild-dashboard.php

app.yourdomain.com/            # Flask API
├── webapp.py
├── api_endpoints.py
└── bot/
    └── templates/
```

## Next Steps

1. **Choose your preferred approach**
2. **Set up WordPress on Bluehost**
3. **Configure Flask as API backend**
4. **Create WordPress custom pages**
5. **Test the integration**

Would you like me to help you implement any of these approaches? 