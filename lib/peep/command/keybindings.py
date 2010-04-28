# vim: fileencoding=utf-8

import sys
import webbrowser
import curses

from decorator import *
from decorator import KEYBINDINGS, HELPS
from message import Message
from peep.const import CONF, MODE

__all__ = ['get']

def get(mode, key):
  return KEYBINDINGS.get(mode).get(key)

@bindkey(MODE.UNREAD, 'j',str(curses.KEY_DOWN))
def next(app):
  'selects the next item in the list'
  return app.ui.grid_panel.next(app.reader.get_unread_entries())

@bindkey(MODE.UNREAD, 'k',str(curses.KEY_UP))
def prev(app):
  'selects the previous item in the list'
  return app.ui.grid_panel.prev(app.reader.get_unread_entries())

@bindkey(MODE.BROWSE, 'j')
def next_browse(app):
  'show the next item'
  if next(app): switch_browse_mode(app)

@bindkey(MODE.BROWSE, 'k')
def prev_browse(app):
  'show the previous item'
  if prev(app): switch_browse_mode(app)

@bindkey(MODE.BROWSE, ' ')
def down(app):
  'show the next page'
  app.ui.browse_panel.down(get_selected_entry(app))

@bindkey(MODE.BROWSE, '-')
def up(app):
  'go back to the previous page'
  app.ui.browse_panel.up(get_selected_entry(app))

@bindkey(MODE.BROWSE, 'J', '\n')
def down1(app):
  'go down one line'
  app.ui.browse_panel.down(get_selected_entry(app), 1)

@bindkey(MODE.BROWSE, 'K')
def up1(app):
  'go up one line'
  app.ui.browse_panel.up(get_selected_entry(app), 1)

@bindkey(MODE.UNREAD, '\n')
@loading
@update_status
def switch_browse_mode(app):
  'show the content of the selected item'
  app.mode = MODE.BROWSE
  entry = get_selected_entry(app)
  app.ui.browse_panel.update(entry)
  app.reader.set_read(entry)

@bindkey(MODE.UNREAD, 'p')
@bindkey(MODE.BROWSE, 'p')
@update_status
def toggle_pin(app):
  'switches the pin status of the selected item'
  entry = get_selected_entry(app)
  app.reader.toggle_pin(entry)
  update_panel(app, entry)

@bindkey(MODE.UNREAD, 's')
@bindkey(MODE.BROWSE, 's')
@update_status
def toggle_star(app):
  'stars or un-stars the selected item'
  entry = get_selected_entry(app)
  app.reader.toggle_star(entry)
  update_panel(app, entry)

@bindkey(MODE.UNREAD, 'm')
@bindkey(MODE.BROWSE, 'm')
@update_status
def toggle_read(app):
  'switches the read status of the selected item'
  entry = get_selected_entry(app)
  app.reader.toggle_read(entry)
  update_panel(app, entry)

@bindkey(MODE.UNREAD, 'A')
@update_status
@confirm(u'Are you sure you want to all items as read?', False)
@loading
def mark_all_as_read(app):
  'mark all items in the current view as read'
  # XXX very very slowly! need asynchronous?
  entries = app.reader.get_unread_entries()
  for entry in entries:
    app.reader.set_read(entry)
  app.ui.grid_panel.update(entries)

@bindkey(MODE.UNREAD, 'O')
@bindkey(MODE.BROWSE, 'O')
@update_status
def open(app):
  'open the selected item by the external browser '
  entry = get_selected_entry(app)
  open_external_browser(app, entry)
  update_panel(app, entry)

@bindkey(MODE.UNREAD, 'o')
@bindkey(MODE.BROWSE, 'o')
@update_status
def open_pinned_entries(app):
  'open the pinned items by the external browser'
  # XXX
  for i in range(int(CONF.browse.max_count)):
    if app.reader.get_pinned_count() == 0: break
    entry = app.reader.get_pinned_entries().pop(0)
    entry['pinned'] = False
    open_external_browser(app, entry)
  if app.mode == MODE.BROWSE:
    app.ui.browse_panel.update_header(get_selected_entry(app))
  else:
    switch_unread_mode(app)

@bindkey(MODE.UNREAD, 'r')
def reload(app):
  'reload the list of unread items'
  app.reader.clear_cache()
  app.ui.grid_panel.clear()
  switch_unread_mode(app)

@bindkey(MODE.BROWSE, 'u', 'q')
@loading
@update_status
def switch_unread_mode(app):
  'show the list of unread items'
  app.mode = MODE.UNREAD
  entries = app.reader.get_unread_entries()
  if entries:
    app.ui.grid_panel.update(entries)
  else:
    app.ui.grid_panel.clear()
    raise Message('Your reading list has no unread items.')

@bindkey(MODE.HELP, 'q')
def back_(app):
  'back to the previous mode'
  # XXX
  {MODE.UNREAD: switch_unread_mode,
   MODE.BROWSE: switch_browse_mode}.get(app.prev_mode)(app)

@bindkey(MODE.UNREAD, 'q')
@confirm(u'Are you sure you want to quit?')
def quit(app):
  'exit peep'
  sys.exit()

@bindkey(MODE.UNREAD, '?')
@bindkey(MODE.BROWSE, '?')
def show_keybindings(app):
  'show key bindings'
  app.ui.help_panel.update(HELPS[app.mode])
  app.mode = MODE.HELP
  raise Message("Press 'q' to quit help.")

# helper functions -----------------------------------------------------------

def get_selected_entry(app):
  return app.reader.get_unread_entries()[app.ui.grid_panel.selected]

def update_panel(app, entry):
  if app.mode == MODE.BROWSE: app.ui.browse_panel.update_header(entry)
  else:                       app.ui.grid_panel.update_row(entry)

def open_external_browser(app, entry):
  try:
    webbrowser.open_new_tab(entry['link'])
    app.reader.set_read(entry)
  except:
    raise Message(u'Failed to open external web browser', 'err')
