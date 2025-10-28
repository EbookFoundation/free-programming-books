# ============================================================
# Gemfile for Jekyll GitHub Pages-compatible site
# Works with themes like "pages-themes/minimal"
# ============================================================

source "https://rubygems.org"

# Jekyll core
gem "jekyll", "~> 4.4.0"

# Core plugins used by GitHub Pages themes
gem "jekyll-remote-theme"   # Loads GitHub-hosted themes
gem "jekyll-seo-tag"        # Adds meta tags for SEO
gem "jekyll-feed"           # Generates an RSS feed
gem "jekyll-sitemap"        # Adds sitemap.xml for better indexing
gem "jemoji"                # Enables emoji support 😊
gem "webrick"               # Required for Ruby 3.x local servers
gem "jekyll-relative-links" # ✅ Fix: add this line

# Group plugins together (Bundler best practice)
group :jekyll_plugins do
  gem "jekyll-remote-theme"
  gem "jekyll-seo-tag"
  gem "jekyll-feed"
  gem "jekyll-sitemap"
  gem "jemoji"
  gem "jekyll-relative-links" # ✅ Also include it here
end
