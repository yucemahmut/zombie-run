class Message(object):
  """A message represents a message that can be shown to a user.
  
  For example, "peter@zrli.org was infected by a zombie!",
               "peter@zrli.org is now a zombie, watch out!"
               
  Messages should be internationalized.  That is a TODO.
  """
  
  def __init__(self):
    pass
  
  def TriggerFor(self, player):
    """Determine whether or not this message should be shown to a particular
    player.
    
    Args:
      player: The player that we are considering showing this message to.
    
    Returns:
      True if this message should be shown to this player.  False otherwise.
    """
    return False
  
  def GetMessage(self, language):
    """Get the string representation of the message that should be shown.
    
    Args:
      language: A string, the ISO language code that the message should be
          internationalized to.  See
          http://www.loc.gov/standards/iso639-2/php/code_list.php for the list
          of language codes.
    
    Returns:
      A unicode or string that should be shown to a player.
    """
    return ""