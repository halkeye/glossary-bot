module.exports = {
  "branches": [
    "master",
  ],
  "tagFormat": "v${version}",
  "plugins": [
    [
      "@semantic-release/commit-analyzer",
      {}
    ],
    [
      "@semantic-release/release-notes-generator",
    ],
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "semantic-release-replace-plugin",
      {
        "replacements": [
          {
            "files": ["gloss/__init__.pyy"],
            "from": "__version__: str = \".*\"",
            "to": "__version__: str = \"${nextRelease.version}\"",
            "results": [
              {
                "file": "foo/__init__.py",
                "hasChanged": true,
                "numMatches": 1,
                "numReplacements": 1
              }
            ],
            "countMatches": true
          }
        ]
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": [
          "gloss/__init__.py"
        ],
        "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
      }
    ]
  ]
}

