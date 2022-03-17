import os
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader

from flytekit import ExecutionParameters, FlyteContext, FlyteContextManager

DEFAULT_DECK_NAME = "default"


class Deck:
    """
    Deck enable users to get customizable and default visibility into their tasks.

    Deck contains a list of renderers (FrameRenderer, MarkdownRenderer) that can
    generate a html file. For example, FrameRenderer can render a DataFrame as an HTML table,
    MarkdownRenderer can convert Markdown string to HTML

    Flyte context saves a list of deck objects, and we use renderers in those decks to render
    the data and create an HTML file when those tasks are executed

    Each task has a least three decks (input, output, default). Input/output decks are
    used to render tasks' input/output data, and the default deck is used to render line plots,
    scatter plots or markdown text. In addition, users can create new decks to render
    their data with custom renderers.
    """

    def __init__(self, name: str, html: Optional[str] = ""):
        self._name = name
        # self.renderers = renderers if isinstance(renderers, list) else [renderers]
        self._html = html
        FlyteContextManager.current_context().user_space_params.decks.append(self)

    def append(self, html: str) -> "Deck":
        assert isinstance(html, str)
        self._html = self._html + "\n" + html
        return self

    @property
    def name(self) -> str:
        return self._name

    @property
    def html(self) -> str:
        return self._html


def _output_deck(task_name: str, new_user_params: ExecutionParameters):
    deck_map: Dict[str, str] = {}
    decks = new_user_params.decks
    ctx = FlyteContext.current_context()

    # output_dir = "/Users/kevin/git/flytekit/deck_outputs"
    output_dir = ctx.file_access.get_random_local_directory()

    for deck in decks:
        _deck_to_html_file(deck, deck_map, output_dir)

    root = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(root, "html")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("template.html")

    deck_path = os.path.join(output_dir, "deck.html")
    with open(deck_path, "w") as f:
        f.write(template.render(metadata=deck_map))

    # TODO: upload deck file to remote filesystems (s3, gcs)
    print(f"{task_name} output flytekit deck html to file://{deck_path}")


def _deck_to_html_file(deck: Deck, deck_map: Dict[str, str], output_dir: str):
    file_name = deck.name + ".html"
    path = os.path.join(output_dir, file_name)
    with open(path, "w") as output:
        deck_map[deck.name] = file_name
        output.write(deck.html)


default_deck = Deck(DEFAULT_DECK_NAME)