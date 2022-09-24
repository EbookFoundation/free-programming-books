# EditorConfig helps developers define and maintain consistent
# coding styles between different editors and IDEs
# editorconfig.org

; top-most EditorConfig file
root = true

; define basic and global for any file
[*]
charset = utf-8
end_of_line = lf
indent_size = 4
indent_style = space
insert_final_newline = true
max_line_length = off
trim_trailing_whitespace = true
curly_bracket_next_line = false
spaces_around_operators = true

; DOS/Windows batch scripts - 
[*.{bat,cmd}]
end_of_line = crlf

; JavaScript files - 
[*.{js,ts}]
curly_bracket_next_line = true
quote_type = single

; JSON files (normal and commented version) - 
[*.{json,jsonc}]
indent_size = 2
quote_type = double

; Make - match it own default syntax
[Makefile]
indent_style = tab

; Markdown files - preserve trail spaces that means break line
[*.{md,markdown}]
trim_trailing_whitespace = false

; PowerShell - match defaults for New-ModuleManifest and PSScriptAnalyzer Invoke-Formatter
[*.{ps1,psd1,psm1}]
charset = utf-8-bom
end_of_line = crlf

; YML config files - match it own default syntax
[*.{yaml,yml}]
indent_size = 2
