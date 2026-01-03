"""Duplicate detection logic mixin for ROM Duplicate Manager.

This module contains duplicate detection and smart selection logic.
"""

import os
import re
from typing import List, Tuple
from rom_duplicate_manager.utils.helpers import extract_languages, extract_version


class DuplicateLogicMixin:
    """Mixin class providing duplicate detection and smart selection logic."""

    def get_file_priority(self, filepath: str) -> Tuple:
        """Calculate file priority for smart selection based on multiple criteria.

        Evaluates files based on:
        - Location (root folder preferred)
        - Quality indicators (proto/beta/demo = lower priority)
        - Version information (newer versions preferred)
        - Language preference matching
        - Video format compatibility
        - File name length (shorter names preferred)

        Args:
            filepath: Full path to the file to evaluate

        Returns:
            Tuple for comparison where lower values = higher priority
        """
        lang_pref = self.language_filter.get()
        filename = os.path.basename(filepath)
        filename_lower = filename.lower()

        # Location priority (root folder preferred)
        root_folder = self.folder.get().replace('\\', '/')
        is_not_in_root = 0 if os.path.dirname(filepath.replace('\\', '/')) == root_folder else 1

        # Quality indicators (lower is worse)
        is_low_priority = 1 if re.search(r'\(proto|\(demo|\(sample|\(beta', filename_lower) else 0

        languages = extract_languages(filename)
        actual_langs = languages - {'Unknown'}
        num_langs = len(actual_langs)
        version = extract_version(filename)
        length = len(filename)
        is_world = 1 if 'World' in languages else 0
        has_lang = 1 if (lang_pref != 'Any' and lang_pref in languages) else 0

        # Video format priority based on language preference
        format_priority = 0
        if lang_pref != 'Any':
            ntsc_regions = ('English-US', 'Japanese', 'Korean', 'Chinese')
            pal_regions = ('English-EU', 'French', 'German', 'Spanish', 'Italian', 'Dutch', 'Portuguese', 'Swedish')
            if lang_pref in ntsc_regions:
                if 'NTSC' in languages:
                    format_priority = 2
                elif 'PAL' in languages:
                    format_priority = 1
                elif 'SECAM' in languages:
                    format_priority = -1
            elif lang_pref in pal_regions:
                if 'PAL' in languages:
                    format_priority = 2
                elif 'SECAM' in languages:
                    format_priority = 1
                elif 'NTSC' in languages:
                    format_priority = -1

        # Return priority tuple (lower values = higher priority)
        return (is_not_in_root, is_low_priority) + tuple(-v for v in version) + \
               (-is_world, -has_lang, -format_priority, -num_langs, length, filename)

    def get_base_file(self, files: List[str]) -> str:
        """Select the best file from a group of duplicates.

        Uses the priority system to determine which file should be kept
        based on quality indicators, version, language preference, etc.

        Args:
            files: List of file paths to evaluate

        Returns:
            Path to the file with the highest priority (lowest priority value)
        """
        return min(files, key=self.get_file_priority)

    def apply_base_suggestions(self) -> None:
        """Apply smart selection suggestions to all duplicate groups.

        For each group of duplicates, identifies the best file using priority
        ranking and marks others for removal if smart select is enabled.
        """
        for parent in self.tree.get_children():
            parent_text = self.tree.item(parent, 'text')
            if parent_text in self.duplicates:
                files = self.duplicates[parent_text]
                base_file = self.get_base_file(files)

                for child in self.tree.get_children(parent):
                    current_tags = list(self.tree.item(child, 'tags'))
                    # Skip manually marked items
                    if 'manual' in current_tags:
                        continue

                    child_path = self.tree.item(child, 'values')[0]
                    current_tags = [t for t in current_tags if t not in ('base', 'to_remove')]

                    if self.smart_select.get():
                        if child_path == base_file:
                            current_tags.append('base')
                        else:
                            current_tags.append('to_remove')

                    self.tree.item(child, tags=tuple(current_tags))

        self.update_tag_colors()
        self.update_status_label()
        self.apply_filter()
