# Wagtail Wordpess Import

An extension for Wagtail CMS that imports WordPress content from an exported XML file into Wagtail models.

## Installation

* Install the package with `pip install wagtail-wordpress-import` (not yet available) but can be installed with pip install -e wagtail-wordpress-import for development.


# Inital setup

Place your XML files somewhere on your disk. The file can have any name you choose.

# Import XML

## To start an import: 
        
`python manage.py import_xml [parent_page_id]` 

- [parent_page_id] is the id of the page in your wagtail site where pages will be created as child pages. If you don't know what that is then choose to edit the page in wagtail admin and look at the url in your browser e.g. `http://www.domain.com/admin/pages/3/edit/` the number after /admin/pages/`3` is the id to use.

### Default command arguments:

- `--model or -m` can be used to specify the Wagtail Page model to use for all imported pages. The default is `PostPage` when it's not specified.

- `--app or -a` can be used to specify the Wagtail App where you have created your Wagtail Page model. The default is `pages` when it's not specified.

TODO add -t help

### Default import command

The package comes with a default command: 

- [import_xml.py](wagtail_wordpress_import/management/commands/import_xml.py)

The configuration is set to import all items in the XML file that have a `<wp:post_type>` = `post` or `page`. The command only imports an item that has `<wp:status>` = `draft` or `publish`. By default each item is created using a Page model of PostPage()

## Changing the import configuration

[View Documentation](docs/prefilters.md)

# XML item fields -> Wagtail model field mapping

TODO 

[View Documentation](docs/mapping.md)

# Creating page models

There is a model mixin in the package which you should use in you own model, at least while running any imports.

TODO

[View Documentation](docs/models.md)

# Utility commands

TODO 

## XML Tag Discovery

`python manage.py extract_xml_mapping` [and add the path to your xml file]

[extract_xml_mapping.py](wagtail_wordpress_import/management/commands/extract_xml_mapping.py)

This command will output a JSON file inside the json folder at the root of your project. The output can help you decide which fields should be included in your import as well as providing a nice short listing of all tags in the XLM for reference.

## XML File Size Reduction

`python manage.py reduce_xml` [and add the path to your xml file]

[reduce_xml.py](wagtail_wordpress_import/management/commands/reduce_xml.py)

This command will output a new xml file with `-reduced` appended to the xml file name and save it in the root `xml` folder.

- Its default behaviour is to remove all comments and comment data.
- It will also output some stats to explain the difference in lines in the xml file.
