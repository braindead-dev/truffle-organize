
import truffle

class organizer:
    def __init__(self):
        self.metadata = truffle.AppMetadata(
            name="organizer",
            description="organizes ur loose files",
            icon="icon.png",
        )
    
    # All tool calls must start with a capital letter! 
    @truffle.tool(
        description="Replace this with a description of the tool.",
        icon="brain"
    )
    @truffle.args(user_input="A description of the argument")
    def organizerTool(self, user_input: str) -> str:
        """
        Replace this text with a basic description of what this function does.
        """
        # There are 
        pass

if __name__ == "__main__":
    app = truffle.TruffleApp(organizer())
    app.launch()
