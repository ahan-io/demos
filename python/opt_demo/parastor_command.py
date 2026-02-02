class ParaStorCommand(object):
    """This is the father class of every ParaStor CLI command.
    """

    def __init__(self):
        """Constructor
        """
        pass
    
    def get_command_name(self):
        """Return the name of this command. If None or an empty string is
        returned, then the file name in which the command exists will be
        the command name.  
        """
        return None
    
    def get_command_help(self):
        """Return the help message of this command.
        """
        return None
    
    def get_command_args(self):
        """Return a list of tuples, each tuple represents an argument of this
        command. The tuple is a four-element tuple which contains the argument
        name, argument type, whether the argument is necessary, the help message
        of the argument. For example:
        ("internal-ips", String, True, "The internal ip list of this node, e.g. 10.0.0.1,10.0.0.2")
        """
        return []
    
    def process(self, args={}):
        """process the command.
        """
        pass
        
    
        
        