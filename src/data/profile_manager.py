import os
import json
import threading
import logging
from typing import Optional, List, Tuple
from src.model.profile import Profile


class ProfileManager:
    def __init__(self, profiles_folder: str, profiles_file_name: str = "profiles.json"):
        """
        Initialize the ProfileManager.
        :param profiles_folder: Folder where the profiles file is stored.
        :param profiles_file_name: File name for the profiles JSON file.
        """
        self.profiles_folder = profiles_folder
        self.profiles_file_name = profiles_file_name
        self.file_path = os.path.join(self.profiles_folder, self.profiles_file_name)
        self.lock = threading.RLock()
        self.profiles_dict = {}  # fast lookup: key=name, value=Profile
        self.profiles_list = []  # maintain order
        os.makedirs(self.profiles_folder, exist_ok=True)
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
        if os.path.exists(self.file_path):
            self.load_profiles()


    def load_profiles(self) -> bool:
        """
        Load profiles from the JSON file.
        :return: True if loading was successful, False otherwise.
        """
        with self.lock:
            try:
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                # Validate and load each profile
                self.profiles_dict.clear()
                self.profiles_list.clear()
                for item in data:
                    try:
                        profile = Profile.from_dict(item)
                        if not profile.name or not profile.url:
                            raise ValueError("Profile name or URL missing")
                        self.profiles_dict[profile.name] = profile
                        self.profiles_list.append(profile)
                    except Exception as e:
                        logging.error(f"Malformed profile data: {item} -- {e}")
                logging.info("Profiles loaded successfully.")
                return True
            except Exception as e:
                logging.error(f"Failed to load profiles: {e}")
                return False

    def save_profiles(self) -> bool:
        """
        Save profiles to the JSON file atomically.
        :return: True if saving was successful, False otherwise.
        """
        with self.lock:
            try:
                # Convert profiles to a list of dictionaries
                data = [p.to_dict() for p in self.profiles_list]
                tmp_file_path = self.file_path + ".tmp"
                with open(tmp_file_path, "w") as f:
                    json.dump(data, f, indent=4)
                os.replace(tmp_file_path, self.file_path)
                logging.info("Profiles saved successfully.")
                return True
            except Exception as e:
                logging.error(f"Failed to save profiles: {e}")
                return False

    def find_profiles(self, name: Optional[str] = None, url: Optional[str] = None) -> List[Profile]:
        """
        Find profiles by name and/or URL.
        :param name: Profile name to search for.
        :param url: Profile URL to search for.
        :return: List of matching Profile objects.
        """
        with self.lock:
            results = []
            for profile in self.profiles_list:
                if name and name.lower() not in profile.name.lower():
                    continue
                if url and url.lower() not in profile.url.lower():
                    continue
                results.append(profile)
            logging.debug(f"find_profiles(name={name}, url={url}) returned {len(results)} results.")
            return results

    def _validate_profile_data(self, name: str, url: str) -> bool:
        """
        Validate that the profile name and URL are not empty and URL is in a proper format.
        :param name: Profile name.
        :param url: Profile URL.
        :return: True if valid, False otherwise.
        """
        if not name.strip():
            logging.error("Profile name is empty.")
            return False
        if not url.strip() or not (url.startswith("http://") or url.startswith("https://")):
            logging.error("Profile URL is empty or malformed.")
            return False
        return True

    def create_profile(self, name: str, url: str, favorites: Optional[List[str]] = None) -> Optional[Profile]:
        """
        Create a new profile.
        :param name: Profile name.
        :param url: Profile URL.
        :param favorites: Optional list of favorites.
        :return: The created Profile, or None if creation failed.
        """
        with self.lock:
            if not self._validate_profile_data(name, url):
                return None
            if name in self.profiles_dict:
                logging.error(f"Profile with name '{name}' already exists.")
                return None

            new_profile = Profile(name, url, favorites)
            # Save current state in case we need to rollback.
            old_profiles_list = list(self.profiles_list)
            old_profiles_dict = dict(self.profiles_dict)

            self.profiles_dict[name] = new_profile
            self.profiles_list.append(new_profile)

            if not self.save_profiles():
                # Rollback changes
                self.profiles_dict = old_profiles_dict
                self.profiles_list = old_profiles_list
                logging.error("Failed to save new profile. Rolling back.")
                return None

            logging.info(f"Profile '{name}' created successfully.")
            return new_profile

    def update_profile(self, updated_profile: Profile) -> bool:
        """
        Update an existing profile.
        :param updated_profile: The Profile object with updated data.
        :return: True if update succeeded, False otherwise.
        """
        with self.lock:
            if updated_profile.name not in self.profiles_dict:
                logging.error(f"Profile '{updated_profile.name}' does not exist.")
                return False

            # Save current state for rollback
            old_profile = self.profiles_dict[updated_profile.name]
            idx = self.profiles_list.index(old_profile)
            backup = old_profile.to_dict()

            # Update profile in both structures
            self.profiles_dict[updated_profile.name] = updated_profile
            self.profiles_list[idx] = updated_profile

            if not self.save_profiles():
                # Rollback update
                self.profiles_dict[updated_profile.name] = Profile.from_dict(backup)
                self.profiles_list[idx] = Profile.from_dict(backup)
                logging.error(f"Failed to update profile '{updated_profile.name}'. Rolling back.")
                return False

            logging.info(f"Profile '{updated_profile.name}' updated successfully.")
            return True

    def get_profile(self, name: str) -> Optional[Profile]:
        """
        Retrieve a profile by name.
        :param name: Profile name.
        :return: The Profile if found, else None.
        """
        with self.lock:
            profile = self.profiles_dict.get(name)
            if profile:
                logging.debug(f"Profile '{name}' retrieved.")
            else:
                logging.debug(f"Profile '{name}' not found.")
            return profile

    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile by name.
        :param name: Profile name.
        :return: True if deletion succeeded, False otherwise.
        """
        with self.lock:
            if name not in self.profiles_dict:
                logging.error(f"Profile '{name}' does not exist.")
                return False

            # Backup current state for rollback.
            profile_to_delete = self.profiles_dict[name]
            old_profiles_list = list(self.profiles_list)
            old_profiles_dict = dict(self.profiles_dict)

            del self.profiles_dict[name]
            try:
                self.profiles_list.remove(profile_to_delete)
            except ValueError:
                logging.error(f"Profile '{name}' not found in profiles list, inconsistency detected.")
                return False

            if not self.save_profiles():
                # Rollback deletion
                self.profiles_dict = old_profiles_dict
                self.profiles_list = old_profiles_list
                logging.error(f"Failed to delete profile '{name}'. Rolling back.")
                return False

            logging.info(f"Profile '{name}' deleted successfully.")
            return True

    def list_profiles(self) -> List[str]:
        """
        List all profile names.
        :return: A list of profile names.
        """
        with self.lock:
            names = [p.name for p in self.profiles_list]
            logging.debug(f"Listing profiles: {names}")
            return names

    def export_profiles(self, export_file_path: str) -> bool:
        """
        Export profiles to a specified file path.
        :param export_file_path: Destination file path.
        :return: True if export succeeded, False otherwise.
        """
        with self.lock:
            try:
                data = [p.to_dict() for p in self.profiles_list]
                tmp_export = export_file_path + ".tmp"
                with open(tmp_export, "w") as f:
                    json.dump(data, f, indent=4)
                os.replace(tmp_export, export_file_path)
                logging.info(f"Profiles exported successfully to '{export_file_path}'.")
                return True
            except Exception as e:
                logging.error(f"Failed to export profiles: {e}")
                return False

    def import_profiles(self, import_file_path: str, overwrite_existing: bool = False) -> Tuple[int, int, int]:
        """
        Import profiles from a specified file.
        :param import_file_path: The JSON file to import.
        :param overwrite_existing: If True, overwrite profiles with the same name.
        :return: A tuple (added, updated, errors)
        """
        added = 0
        updated = 0
        errors = 0

        with self.lock:
            try:
                with open(import_file_path, "r") as f:
                    imported_data = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load import file '{import_file_path}': {e}")
                return (added, updated, 1)

            # Backup current state for rollback in case of failure
            backup_dict = dict(self.profiles_dict)
            backup_list = list(self.profiles_list)

            for item in imported_data:
                try:
                    imp_profile = Profile.from_dict(item)
                    if not self._validate_profile_data(imp_profile.name, imp_profile.url):
                        raise ValueError("Invalid profile data")
                    if imp_profile.name in self.profiles_dict:
                        if overwrite_existing:
                            # Update existing profile
                            idx = self.profiles_list.index(self.profiles_dict[imp_profile.name])
                            self.profiles_list[idx] = imp_profile
                            self.profiles_dict[imp_profile.name] = imp_profile
                            updated += 1
                        else:
                            logging.info(f"Profile '{imp_profile.name}' exists and will not be overwritten.")
                    else:
                        # Add new profile
                        self.profiles_dict[imp_profile.name] = imp_profile
                        self.profiles_list.append(imp_profile)
                        added += 1
                except Exception as e:
                    logging.error(f"Error importing profile: {item} -- {e}")
                    errors += 1

            if not self.save_profiles():
                # Rollback if save fails
                self.profiles_dict = backup_dict
                self.profiles_list = backup_list
                logging.error("Failed to save imported profiles. Rolling back import operation.")
                return (0, 0, errors + 1)

            logging.info(f"Import completed: {added} added, {updated} updated, {errors} errors.")
            return (added, updated, errors)


# --- Example usage ---

if __name__ == "__main__":
    # Configure logging output to the console.
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

    profiles_dir = "./profiles_data"
    manager = ProfileManager(profiles_dir)

    # Create a profile
    p = manager.create_profile("User1", "http://example.com/stream", favorites=["channel1", "channel2"])
    if p:
        print("Profile created:", p)

    # List profiles
    print("Profiles:", manager.list_profiles())

    # Update profile
    if p:
        p.url = "https://example.com/newstream"
        if manager.update_profile(p):
            print("Profile updated:", manager.get_profile("User1"))

    # Export profiles
    export_path = os.path.join(profiles_dir, "exported_profiles.json")
    if manager.export_profiles(export_path):
        print("Profiles exported to", export_path)

    # Import profiles (simulate import; in a real scenario, the file would come from elsewhere)
    added, updated, errors = manager.import_profiles(export_path, overwrite_existing=True)
    print(f"Imported profiles: {added} added, {updated} updated, {errors} errors.")

    # Delete profile
    if manager.delete_profile("User1"):
        print("Profile 'User1' deleted.")
    print("Final profiles:", manager.list_profiles())
