Package enhancement
====

Currently, there are two main ways to enhance your own packages with Talon HUD, namely documentation and walkthroughs.
Both of them work by registering files to the Talon HUD if it is available, so it won't cause slowdowns or crashes for non-Talon HUD users.

For an example on how to add stuff, you can look at the file [load_talon_hud_docs.py](load_talon_hud_docs.py) in the docs folder.
It is recommended that you have a separate directory where you keep all the files related to your documentation or walkthroughs.

For all of these options, you should have a look at the part about rich text in the [content publishing documentation](content/README.md) as it gives an outline of all the possible rich text tokens you can use.
You should think ahead if the explanation you are making for the users is meant to be a quick reference, or an exploration of the options.
A documentation page is easier to scan, so it lends itself well for a quick reference. Whereas a walkthrough is harder to scan, but much easier to process, as it let's the user focus on one thing at a time.

# Documentation

To add documentation to the Talon HUD toolkit, you can use the `user.hud_add_documentation` action.

These are the values that you can give to the `user.hud_add_documentation` action.
- Title: The title of the documentation you're adding. This will be shown as a header in the panel showing when a user accesses the documentation either by navigating to it or by saying `toolkit documentation`.
- Description: A short description of what the documentation is about. This will be shown next to the title in the documentation panel.
- Filename: An absolute path to the file containing the documentation.

For an example, you can have a look at the [hud_widget_documentation.txt](hud_widget_documentation.txt) file in the docs directory.

# Walkthroughs

A walkthrough is a step by step guide to give the user a sense of what kind of things they can do with your package.
Every step can contain one or more voice commands that the user must say before the step is advanced.
Every step can have a specific context linked to it as well, so that the user is guided towards the right situation to try out the voice commands.
As a bonus, each walkthrough the user has finished will be marked with a checkmark on the walkthrough overview.

Talon HUD uses one to give a brief tour of the possibilities and the content.

Adding a walkthrough to the `toolkit walkthrough` panel can be done using the `user.hud_add_walktrough` action.
This action takes only two values.
- Title: The title of the walkthrough that is being added, this will show up in the options panel.
- Filename: An absolute path to the JSON file containing the walkthrough data. 

As an example JSON, you can have a look at the hud_walkthrough.json file in the docs directory.

Basically, the file is built up as a list of steps. Each step can contain the following information.

```
{
    "content": "", # The text of the walkthrough step, with <cmd@ these markers /> to denote voice commands that can be said.
	"context_hint": "", # The text that is displayed when the user is in the wrong context, to guide them back on the right place where the voice commands are active.
	"tags": [], # A list of tags that must be active, otherwise the context_hint will be shown to guide the user back to the right tags.
	"modes": [], # A list of modes that must be active, otherwise the context_hint will be shown to guide the user back to the right modes.
	"app": "" # The name of the app that the user must be in, otherwise the context_hint will be shown.
}
```

If you are unsure if your JSON formatting is correct, you can test it on [jsonlint.com](https://jsonlint.com/) for errors.