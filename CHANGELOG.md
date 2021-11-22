# Changelog

## [Unreleased](https://github.com/torchbox/wagtail-wordpress-import/tree/HEAD)

[Full Changelog](https://github.com/torchbox/wagtail-wordpress-import/compare/885bd32522e3742bf17d8a284056aebf21a86aad...HEAD)

**Implemented enhancements:**

- Add extra tooling command [\#92](https://github.com/torchbox/wagtail-wordpress-import/issues/92)
- Move pull request template [\#90](https://github.com/torchbox/wagtail-wordpress-import/issues/90)
- Allow mapping file overrides [\#22](https://github.com/torchbox/wagtail-wordpress-import/issues/22)
- Give the package a new name [\#19](https://github.com/torchbox/wagtail-wordpress-import/issues/19)
- Add ability to specify wp:post\_type [\#16](https://github.com/torchbox/wagtail-wordpress-import/issues/16)
- Refine the delete\_imported\_xml command [\#15](https://github.com/torchbox/wagtail-wordpress-import/issues/15)
- The date appended to the log file name is not easy to read [\#14](https://github.com/torchbox/wagtail-wordpress-import/issues/14)
- Remove unnecessary package config [\#13](https://github.com/torchbox/wagtail-wordpress-import/issues/13)
- Refactor/block builder [\#64](https://github.com/torchbox/wagtail-wordpress-import/pull/64) ([nickmoreton](https://github.com/nickmoreton))

**Fixed bugs:**

- CI testing matrix needs updating [\#89](https://github.com/torchbox/wagtail-wordpress-import/issues/89)
- Image and Document model loading [\#60](https://github.com/torchbox/wagtail-wordpress-import/issues/60)

**Closed issues:**

- wondering why this is separate and not a key in ``OPTIONS`` on the pre-filter config [\#61](https://github.com/torchbox/wagtail-wordpress-import/issues/61)
- Base README.md not yet complete [\#54](https://github.com/torchbox/wagtail-wordpress-import/issues/54)
- Docs: remove reference to processes that don't exist yet [\#52](https://github.com/torchbox/wagtail-wordpress-import/issues/52)
- Help text missing xml\_file\_path in example [\#51](https://github.com/torchbox/wagtail-wordpress-import/issues/51)
- docs referring to bleach\_filters could be clearer [\#50](https://github.com/torchbox/wagtail-wordpress-import/issues/50)
- Use individual rules instead of the whole style. [\#47](https://github.com/torchbox/wagtail-wordpress-import/issues/47)
- analyze\_html\_content is broken [\#42](https://github.com/torchbox/wagtail-wordpress-import/issues/42)
- Can we combine some filters? [\#41](https://github.com/torchbox/wagtail-wordpress-import/issues/41)
- What if there's another style inserted in between? [\#40](https://github.com/torchbox/wagtail-wordpress-import/issues/40)
- I think these module paths are a bit long [\#39](https://github.com/torchbox/wagtail-wordpress-import/issues/39)
- Should we use an id for the parent? [\#8](https://github.com/torchbox/wagtail-wordpress-import/issues/8)
- What does this line do? [\#7](https://github.com/torchbox/wagtail-wordpress-import/issues/7)
- Typo in runxml [\#6](https://github.com/torchbox/wagtail-wordpress-import/issues/6)
- runxml returns LookupError: No installed app with label 'pages' [\#5](https://github.com/torchbox/wagtail-wordpress-import/issues/5)
- Naming of management commands [\#4](https://github.com/torchbox/wagtail-wordpress-import/issues/4)
- Reduce command changes the provided filename [\#3](https://github.com/torchbox/wagtail-wordpress-import/issues/3)

**Merged pull requests:**

- Move pull request template [\#91](https://github.com/torchbox/wagtail-wordpress-import/pull/91) ([nickmoreton](https://github.com/nickmoreton))
- Change ci testing matrix [\#88](https://github.com/torchbox/wagtail-wordpress-import/pull/88) ([nickmoreton](https://github.com/nickmoreton))
- Analyse XML file [\#87](https://github.com/torchbox/wagtail-wordpress-import/pull/87) ([nickmoreton](https://github.com/nickmoreton))
- Add pull request template [\#86](https://github.com/torchbox/wagtail-wordpress-import/pull/86) ([nimasmi](https://github.com/nimasmi))
- Run make migrations on test site example [\#83](https://github.com/torchbox/wagtail-wordpress-import/pull/83) ([nickmoreton](https://github.com/nickmoreton))
- Change CI Pipeline test matrix [\#82](https://github.com/torchbox/wagtail-wordpress-import/pull/82) ([nickmoreton](https://github.com/nickmoreton))
- \#64 developer tooling docs [\#79](https://github.com/torchbox/wagtail-wordpress-import/pull/79) ([nickmoreton](https://github.com/nickmoreton))
- \#84 use custom image and document models [\#78](https://github.com/torchbox/wagtail-wordpress-import/pull/78) ([nickmoreton](https://github.com/nickmoreton))
- 'Lint' documentation writing style [\#77](https://github.com/torchbox/wagtail-wordpress-import/pull/77) ([nimasmi](https://github.com/nimasmi))
- fix/\#79-reduce-command-flexibility [\#76](https://github.com/torchbox/wagtail-wordpress-import/pull/76) ([nickmoreton](https://github.com/nickmoreton))
- update main README file [\#75](https://github.com/torchbox/wagtail-wordpress-import/pull/75) ([nickmoreton](https://github.com/nickmoreton))
- \#82 change help text for import command [\#74](https://github.com/torchbox/wagtail-wordpress-import/pull/74) ([nickmoreton](https://github.com/nickmoreton))
- fix/\#80 headings in richtext [\#73](https://github.com/torchbox/wagtail-wordpress-import/pull/73) ([nickmoreton](https://github.com/nickmoreton))
- fix/\#80-yoast-import-error [\#72](https://github.com/torchbox/wagtail-wordpress-import/pull/72) ([nickmoreton](https://github.com/nickmoreton))
- \#70 generate streamfield block [\#71](https://github.com/torchbox/wagtail-wordpress-import/pull/71) ([nickmoreton](https://github.com/nickmoreton))
- \#68 shortcode prefilter registration [\#70](https://github.com/torchbox/wagtail-wordpress-import/pull/70) ([nickmoreton](https://github.com/nickmoreton))
- \#66 write block prefilter class [\#69](https://github.com/torchbox/wagtail-wordpress-import/pull/69) ([nickmoreton](https://github.com/nickmoreton))
- \#69 filters in import flow [\#68](https://github.com/torchbox/wagtail-wordpress-import/pull/68) ([nickmoreton](https://github.com/nickmoreton))
- \#39 importing categories [\#66](https://github.com/torchbox/wagtail-wordpress-import/pull/66) ([nickmoreton](https://github.com/nickmoreton))
- \#42 import documents [\#57](https://github.com/torchbox/wagtail-wordpress-import/pull/57) ([nickmoreton](https://github.com/nickmoreton))
- \#43 import yoast content [\#56](https://github.com/torchbox/wagtail-wordpress-import/pull/56) ([nickmoreton](https://github.com/nickmoreton))
- Integration/sprint 6 [\#55](https://github.com/torchbox/wagtail-wordpress-import/pull/55) ([nickmoreton](https://github.com/nickmoreton))
- \#22 filter the blocks [\#49](https://github.com/torchbox/wagtail-wordpress-import/pull/49) ([nickmoreton](https://github.com/nickmoreton))
- \#53 Use single style rule [\#48](https://github.com/torchbox/wagtail-wordpress-import/pull/48) ([nickmoreton](https://github.com/nickmoreton))
- Implement configurable pre filters [\#46](https://github.com/torchbox/wagtail-wordpress-import/pull/46) ([nickmoreton](https://github.com/nickmoreton))
- Revert "Implement configurable pre filters" [\#45](https://github.com/torchbox/wagtail-wordpress-import/pull/45) ([nickmoreton](https://github.com/nickmoreton))
- Revert "\#49 Split blocks unit tests" [\#43](https://github.com/torchbox/wagtail-wordpress-import/pull/43) ([kaedroho](https://github.com/kaedroho))
- \#49 Split blocks unit tests [\#38](https://github.com/torchbox/wagtail-wordpress-import/pull/38) ([nickmoreton](https://github.com/nickmoreton))
- Logging around image imports [\#37](https://github.com/torchbox/wagtail-wordpress-import/pull/37) ([nickmoreton](https://github.com/nickmoreton))
- \#13 pre-filter documentation [\#36](https://github.com/torchbox/wagtail-wordpress-import/pull/36) ([nickmoreton](https://github.com/nickmoreton))
- Implement configurable pre filters [\#35](https://github.com/torchbox/wagtail-wordpress-import/pull/35) ([nickmoreton](https://github.com/nickmoreton))
- Normalize styles filter [\#34](https://github.com/torchbox/wagtail-wordpress-import/pull/34) ([nickmoreton](https://github.com/nickmoreton))
- Remove python 3.7 support [\#32](https://github.com/torchbox/wagtail-wordpress-import/pull/32) ([nickmoreton](https://github.com/nickmoreton))
- Implement wordpress item class [\#31](https://github.com/torchbox/wagtail-wordpress-import/pull/31) ([nickmoreton](https://github.com/nickmoreton))
- Shortcodes analysis [\#30](https://github.com/torchbox/wagtail-wordpress-import/pull/30) ([kaedroho](https://github.com/kaedroho))
- Report on shortcodes [\#29](https://github.com/torchbox/wagtail-wordpress-import/pull/29) ([kaedroho](https://github.com/kaedroho))
- Rename package to wagtail\_wordpress\_import [\#28](https://github.com/torchbox/wagtail-wordpress-import/pull/28) ([nickmoreton](https://github.com/nickmoreton))
- Create content stream blocks [\#27](https://github.com/torchbox/wagtail-wordpress-import/pull/27) ([nickmoreton](https://github.com/nickmoreton))
- Implement bleach and filter functions [\#26](https://github.com/torchbox/wagtail-wordpress-import/pull/26) ([nickmoreton](https://github.com/nickmoreton))
- Analysis weighting and style values report [\#25](https://github.com/torchbox/wagtail-wordpress-import/pull/25) ([nickmoreton](https://github.com/nickmoreton))
- Implemented analyze\_html\_content management command [\#24](https://github.com/torchbox/wagtail-wordpress-import/pull/24) ([kaedroho](https://github.com/kaedroho))
- Allow xml source files in root of app [\#23](https://github.com/torchbox/wagtail-wordpress-import/pull/23) ([nickmoreton](https://github.com/nickmoreton))
- Add extra command line args [\#21](https://github.com/torchbox/wagtail-wordpress-import/pull/21) ([nickmoreton](https://github.com/nickmoreton))
- Change log file date format [\#20](https://github.com/torchbox/wagtail-wordpress-import/pull/20) ([nickmoreton](https://github.com/nickmoreton))
- Refine the delete command [\#18](https://github.com/torchbox/wagtail-wordpress-import/pull/18) ([nickmoreton](https://github.com/nickmoreton))
- Remove unused config [\#17](https://github.com/torchbox/wagtail-wordpress-import/pull/17) ([nickmoreton](https://github.com/nickmoreton))
- change-links-in-docs [\#12](https://github.com/torchbox/wagtail-wordpress-import/pull/12) ([nickmoreton](https://github.com/nickmoreton))
- Add tests [\#11](https://github.com/torchbox/wagtail-wordpress-import/pull/11) ([nickmoreton](https://github.com/nickmoreton))
- Issues/ticket \#33 [\#10](https://github.com/torchbox/wagtail-wordpress-import/pull/10) ([nickmoreton](https://github.com/nickmoreton))
- Documentation [\#9](https://github.com/torchbox/wagtail-wordpress-import/pull/9) ([nickmoreton](https://github.com/nickmoreton))
- Sprint 1 [\#2](https://github.com/torchbox/wagtail-wordpress-import/pull/2) ([nickmoreton](https://github.com/nickmoreton))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
