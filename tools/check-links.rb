#!/usr/bin/env ruby

# Copyright (C) 2013 Dmtiry Yakimenko (detunized@gmail.com)
# Released under the MIT License (http://opensource.org/licenses/MIT)

# Run via Bundler:
# $ bundle exec ./check-links.rb
#
# Or just like that if all the dependencies are installed:
# $ ./check-list.rb

# This script checks if the books on the list are accessible. When <verify snippet="..." />
# tag is provided, the content is checked against it. The snippet should be present in the
# body of the response as is (not HTML tags are processed or stripped).
# <verify> tag was invented since I couldn't find a way to embed a comment into a markdown file.
# GitHub seems to be stripping unknown tags out. So it works.

# TODO:
#   - silent mode
#   - log failures in machine readable format
#   - disable color
#   - possibly relax regex a bit
#   - display book title instead along with the URL

require "httparty"
require "colorize"

BOOK_LIST = "../free-programming-books.md"

# Make stdout flush every time something is printed
$stdout.sync = true

def ok
    puts "OK".green
end

def failed reason
    puts "#{'failed'.red} (#{reason})"
end

books = File.read(BOOK_LIST).scan(%r{\((https?://.*?)\)(?:\s*\<verify snippet="(.*?)" /\>)?})
digits = books.size.to_s.size
books.each_with_index do |book, index|
    url, snippet = *book
    print "[%#{digits}d/#{books.size}] Checking %s " % [index + 1, url]
    begin
        response = HTTParty.get(url).response
        if response.is_a? Net::HTTPOK
            if !snippet || response.body.include?(snippet)
                ok
            else
                failed "content doesn't match"
            end
        else
            failed "code: #{response.code}"
        end
    rescue StandardError => e
        failed "error: '#{e}'"
    end
end
