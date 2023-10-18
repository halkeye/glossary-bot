# Changelog

## Unreleased (2023-10-17)
[Compare the full difference.](https://github.com/halkeye/glossary-bot/compare/2.0.1...HEAD)

### Other

- Document releasing. [0c51459](https://github.com/halkeye/glossary-bot/commit/0c514598540a27944afaf645faa811674faf034e)
    
- Configure bump-my-version. [12f6bfd](https://github.com/halkeye/glossary-bot/commit/12f6bfdf5911b39567dfe0d3478dd19bcfdf3db5)
    
- Cleanup pip install docs. [b605f2d](https://github.com/halkeye/glossary-bot/commit/b605f2d7e45dd9b482dc0cef58d49353365bc1ff)
    
### Updates

- Changelog. [1c2eb28](https://github.com/halkeye/glossary-bot/commit/1c2eb28c114920564cad621f7643bf9cb0411657)
    
## 2.0.1 (2023-10-18)
[Compare the full difference.](https://github.com/halkeye/glossary-bot/compare/2.0.0...2.0.1)

### New

- Add legacy setup.py just in case. [41420e9](https://github.com/halkeye/glossary-bot/commit/41420e9bfe29b0cdcca86816fb0b1a150bd95a66)

## 2.0.0 (2023-10-17)

- Initial my version
- Major refactor to support mysql as well as postgres
- fuzzy matching in memory instead of postgres specific logic
- switch to python-bolt for slack communication, which lets us run in websocket mode (no public incoming access needed)
- /glossary is for you only, @glossary-bot is for public
