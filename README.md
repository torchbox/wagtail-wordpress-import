# Wagtail xmlimport

An extension for importing model data from a xml file into a Wagail project.

It's intended that the data can be used to create page models, image models, document models and more.

Currently available models:

    Page

`Inital work is to import from a Wordpress xml export but it should be possible to use it for other xml data sources.`

## Installation

* Install the package with `pip install wagtail-xmlimport` (not yet available) but can be installed with pip install -e wagtail-xmlimport for development.

* Add `wagtail_xmlimport` to INSTALLED_APPS in your project

# Inital setup

## It's a good idead to include this and other folders listed below in your .gitignore to avoid exposing potentially private data to the world.

Place your xml files inside a folder `xml` at the root of your project. You can name them whatever you want.

Add a `json` folder to the root of your project. There's a optional `discovery` command that will need to write to that folder. Again add the folder to your `.gitignore` file

## XML -> Wagtail model mapping

* The general process to import the xml file is
    
    1. Create a mapping file using the `discovery` command with the xml file to use.
    2. Adjust the resulting json file to your needs (see blow)
    3. Run the import command on the created json file

`The import command needs the json mapping file to exist to know which fields to include in the import as well as the source xml file` Those fields will be part of your Wagtail model.

# Mapping

A simple mapping file could be: (It always needs the root item.) See below how to get there using the discovery command but you could write the file from scratch.

`Sample is for wordpress`

```
{
  "root": {
    "//[ The xml file to use ]//": "",
    "file": ["myxmlfile.xml"],
    "//[ Default Value. The tag for each page in the xml file tree ]//": "",
    "tag": ["item"],
    "//[ The page type in xml tag ]//": "",
    "type": ["page"],
    "//[ Default Value. The model to import to ]//": "",
    "model": ["PostPage"],
    "//[ The statuses to import ]//": "",
    "status": ["publish", "draft"]
  },
  "title": ["title", "required"],
  "link": [],
  "pubDate": [],
  "dc:creator": [],
  "guid": [],
  "description": [],
  "content:encoded": ["body", "stream:raw_html:*auto_p", "required"],
  "excerpt:encoded": [],
  "wp:post_id": ["wp_post_id"],
  "wp:post_date": ["%%date", "first_published_at:last_published_at:latest_revision_created_at"],
  "wp:post_date_gmt": [],
  "wp:post_modified": [],
  "wp:post_modified_gmt": [],
  "wp:comment_status": [],
  "wp:ping_status": [],
  "wp:post_name": ["slug", "*slugify", "required"],
  "wp:status": ["__status"],
  "wp:post_parent": [],
  "wp:menu_order": [],
  "wp:post_type": ["wp_post_type"],
  "wp:post_password": [],
  "wp:is_sticky": [],
  "wp:postmeta": [],
  "wp:postmeta/wp:meta_key": [],
  "wp:postmeta/wp:meta_value": [],
  "category": []
}
```

NOTES: 

The special markers `__` and `%%` indicate fields that don't directly relate to a wagtail model field and have extra processing. They may end up in a wagtail model field after processing. Field without markers are directly imprted.

To process marked fields you will need to write a processor. (Docs to come)

Each xml tag can have 1, 2 or 3 parameters in a list.

  1. Wagtail field name (as in your page model)
  2. Field processing (for fields like stream field and slugs)
  3. Field attrubites (if a field is required)

Tags with an empty parameters list are ignored. They can be removed to simpify it.

In the root item:

* `"file"` is the name of the xml file to load.
* `"tag"` is the tag name that is the parent tag of all the data tags you want to include in the import.
* `"type"` is the item type to be imported.
* `"model"` is the model the data will be imported to (Wagtail model name)
* `"status"` is the status to pass through to the imported page

### Using the discover command

You can import a file as below... A shorter example

```
<?xml version="1.0"?>
<catalog>
   <book id="bk101">
      <author>Gambardella, Matthew</author>
      <title>XML Developer's Guide</title>
      <genre>Computer</genre>
      <price>44.95</price>
      <publish_date>2000-10-01</publish_date>
      <description>An in-depth look at creating applications 
      with XML.</description>
   </book>
```

and the output of discover for this xml would be.

```
{
  "root": [],
  "book_id": "id",
  "author": [],
  "title": [],
  "genre": [],
  "price": [],
  "publish_date": [],
  "description": []
}
```

and you would alter the file to something like the one at the begining of the Mapping section. 

# Importing

To start an import, in your project run `python manage.py runxml` with a parameter of the json file name saved earlier.

# Large XML files

To help with speeding up the import process there is a management command.

`python manage.py reduce` with a parameter of the xml file name you want to work with. It will produce a new file with the same name and `-reduced` appended. This is the xml file name to add to your mapping.json file