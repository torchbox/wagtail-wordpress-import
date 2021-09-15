# Wagtail xmlimport

An extension for importing model data from a xml file into a Wagail project.

It's intended that the data can be used to create page models, image models, document models and more.

`Inital work is to import from a Wordpress xml export but it should be possible to use it for other xml data sources.`





## Installation

* Install the package with `pip install wagtail-xmlimport` (not yet available) but can be installed with pip install -e wagtail-xmlimport for development.

* Add `wagtail_xmlimport` to INSTALLED_APPS in your project





# Inital setup

Place your xml files inside a folder called `xml` at the root of your project. The file can have any name you choose.

### It's a good idead to include these folders to your .gitignore to avoid exposing potentially private data to the world.





# Import XML

## To start an import: 
        
`python manage.py import_xml [parent_page_id]` 

- [parent_page_id] is the id of the page in your wagtail site where pages will be created as child pages. If you don't know what that is then choose to edit the page in wagtail admin and look at the url in your browser e.g. `http://www.domain.com/admin/pages/3/edit/` the number after /admin/pages/`3` is the id to use.

### Default command arguments:

- `--model or -m` can be used to specify the Wagtail Page model to use for all imported pages. The default is `PostPage` when it's not specified.

- `--app or -a` can be used to specify the Wagtail App where you have created your Wagtail Page model. The default is `pages` when it's not specified.

### Default import command

The package comes with a default command: 

- [wagtail-xmlimport/wagtail_xmlimport/management/commands/import_xml.py](./wagtail-xmlimport/wagtail_xmlimport/management/commands/import_xml.py)

The configuration is set to import all items in the xml file that have a `<wp:post_type>` = `post` or `page`. Also the command only imports an item that has `<wp:status>` = `draft` or `publish`

### You can create you own command to import the xml file.
[View Documentation](./wagtail-xmlimport/docs/commands.md)





# XML item fields -> Wagtail model field mapping

There is a built in wordpress -> wagtail mapping file in the package. You can choose to extend the mapping and add your own methods to process each item.

[View Documentation](./wagtail-xmlimport/docs/mapping.md)




# Creating page models

There is a model mixin in the package which you should use in you own model, at least while running any imports.

[View Documentation](wagtail-xmlimport/docs/models.md)



# Utility commands

## XML Tag Discovery

`python manage.py extract_xml_mapping` [and add the path to your xml file]

[wagtail-xmlimport/wagtail_xmlimport/management/commands/extract_xml_mapping.py](wagtail-xmlimport/wagtail_xmlimport/management/commands/extract_xml_mapping.py)

This command will output a json file inside the json folder at the root of your project. The output can help you decide whcih fields should be included in your import as well as providing a nice short listing of all tags in the xml for reference.

## XML File Size Reduction

`python manage.py reduce_xml` [and add the path to your xml file]

[wagtail-xmlimport/wagtail_xmlimport/management/commands/reduce_xml.py](wagtail-xmlimport/wagtail_xmlimport/management/commands/reduce_xml.py)

This command will output a new xml file with `-reduced` appended to the xml file name and save it in the root `xml` folder.

- It's default behaviour is to remove all comments and comment data.
- It will also output some stats to explain the difference in lines in the xml file.