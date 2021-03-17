npm run build
# Remove-Item -r -Path ../static/css ../static/js
Copy-Item -r -fo build/static/* ../static
Copy-Item -r -fo build/index.html ../templates/react-editor.html