import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import truffle
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DesktopOrganizer:
    """
    A Truffle App that intelligently organizes files on macOS Desktop into appropriate folders
    using LLM capabilities to determine the best organization structure.
    """
    def __init__(self) -> None:
        self.metadata = truffle.AppMetadata(
            name="organizer",
            description="Intelligently organizes files on your Desktop using AI",
            icon="folder.fill"
        )
        self.client = truffle.TruffleClient()
        self.desktop_path = str(Path.home() / "Desktop")
        logger.info(f"Initialized DesktopOrganizer with desktop path: {self.desktop_path}")

    @truffle.tool(
        description="Shows the current state of your Desktop",
        icon="info.circle.fill"
    )
    @truffle.args(
        include_hidden="Whether to include hidden files in the status"
    )
    def show_status(self, include_hidden: bool = False) -> str:
        """Shows what files and folders are currently on your Desktop."""
        try:
            if not os.path.exists(self.desktop_path):
                return "Desktop path not found!"

            files = []
            folders = []
            
            for item in os.listdir(self.desktop_path):
                if not include_hidden and item.startswith('.'):
                    continue
                    
                item_path = os.path.join(self.desktop_path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
                else:
                    files.append(item)

            status = ["Desktop Status:"]
            status.append(f"\nTotal Items: {len(files) + len(folders)}")
            
            if folders:
                status.append("\nFolders:")
                for folder in sorted(folders):
                    status.append(f"  - {folder}")

            if files:
                status.append("\nFiles:")
                for file in sorted(files):
                    status.append(f"  - {file}")

            return "\n".join(status)
        except Exception as e:
            return truffle.ReportError(e)

    @truffle.tool(
        description="Analyzes files and suggests organization categories",
        icon="brain.head.profile"
    )
    @truffle.args(
        files="List of filenames to analyze"
    )
    def analyze_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Uses AI to analyze files and suggest appropriate categories."""
        if not files:
            return {}

        try:
            # Create a prompt for the LLM
            prompt = f"""Given these files:
{json.dumps(files, indent=2)}

Create appropriate categories and assign each file to one category.
Consider:
- File extensions and types
- Naming patterns and content hints
- Common desktop organization practices
- Group similar files together
- Use intuitive category names

Return ONLY a JSON object where:
- Keys are category names (clear, simple names)
- Values are lists of filenames that belong in that category"""

            # Get categorization from LLM
            response = self.client.chat_completion([
                {"role": "system", "content": "You are an expert at organizing files into logical categories. You ONLY respond with valid JSON."},
                {"role": "user", "content": prompt}
            ])

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error analyzing files: {str(e)}")
            # Fallback to basic categorization
            extensions = {}
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if not ext:
                    ext = "No Extension"
                category = {
                    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
                    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents", ".txt": "Documents",
                    ".mp4": "Videos", ".mov": "Videos", ".avi": "Videos",
                    ".mp3": "Audio", ".wav": "Audio", ".m4a": "Audio",
                    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
                    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code"
                }.get(ext, "Other")
                
                extensions.setdefault(category, []).append(file)
            return extensions

    @truffle.tool(
        description="Organizes your Desktop files into folders",
        icon="folder.fill"
    )
    @truffle.args(
        dry_run="If True, shows what would be done without actually moving files"
    )
    def organize(self, dry_run: bool = False) -> str:
        """
        Organizes Desktop files into appropriate folders based on AI analysis.
        Returns a summary of actions taken.
        """
        try:
            # Get list of files to organize
            files = [f for f in os.listdir(self.desktop_path) 
                    if not f.startswith('.') and 
                    os.path.isfile(os.path.join(self.desktop_path, f))]
            
            if not files:
                return "No files to organize on the desktop."

            # Get AI-suggested categorization
            categories = self.analyze_files(files)
            
            if dry_run:
                # Just show what would be done
                summary = ["Preview of organization plan:"]
                for category, files in categories.items():
                    summary.append(f"\n{category}:")
                    for file in files:
                        summary.append(f"  - {file}")
                return "\n".join(summary)

            # Actually organize the files
            moved_files = {}
            skipped_files = []

            for category, category_files in categories.items():
                for file in category_files:
                    src_path = os.path.join(self.desktop_path, file)
                    if not os.path.exists(src_path):
                        skipped_files.append(f"{file} (not found)")
                        continue

                    # Create category folder
                    folder_path = os.path.join(self.desktop_path, category)
                    os.makedirs(folder_path, exist_ok=True)

                    # Handle filename conflicts
                    dest_path = os.path.join(folder_path, file)
                    if os.path.exists(dest_path):
                        base, ext = os.path.splitext(file)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_name = f"{base}_{timestamp}{ext}"
                        dest_path = os.path.join(folder_path, new_name)

                    try:
                        shutil.move(src_path, dest_path)
                        moved_files.setdefault(category, []).append(file)
                    except Exception as e:
                        skipped_files.append(f"{file} ({str(e)})")

            # Prepare summary
            summary = ["Organization Complete!"]
            for category, files in moved_files.items():
                summary.append(f"\n{category} ({len(files)} files):")
                for file in sorted(files):
                    summary.append(f"  - {file}")

            if skipped_files:
                summary.append("\nSkipped files:")
                for file in sorted(skipped_files):
                    summary.append(f"  - {file}")

            return "\n".join(summary)
        except Exception as e:
            return truffle.ReportError(e)

def main():
    """Main function to run the app directly."""
    try:
        organizer = DesktopOrganizer()
        
        # Show current status
        print("\nCurrent Desktop Status:")
        print("-" * 50)
        print(organizer.show_status())
        
        # Ask if user wants to organize
        response = input("\nWould you like to organize your desktop? (y/n): ")
        if response.lower() == 'y':
            # First show a preview
            print("\nHere's what I plan to do:")
            print("-" * 50)
            print(organizer.organize(dry_run=True))
            
            # Ask for confirmation
            confirm = input("\nProceed with organization? (y/n): ")
            if confirm.lower() == 'y':
                print("\nOrganizing desktop...")
                print("-" * 50)
                print(organizer.organize())
            else:
                print("\nOperation cancelled.")
        else:
            print("\nOperation cancelled.")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        # First try to launch as a Truffle app
        app = truffle.TruffleApp(DesktopOrganizer())
        app.launch()
    except Exception as e:
        logger.error(f"Failed to launch as Truffle app: {str(e)}")
        logger.info("Falling back to command-line interface")
        # If that fails, fall back to command-line interface
        main() 