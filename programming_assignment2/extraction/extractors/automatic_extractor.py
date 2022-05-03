from .base_extractor import BaseExtractor
from bs4 import BeautifulSoup, NavigableString, Comment
from os.path import join
import glob
from enum import Enum

class Match(Enum):
    NO_MATCH = 1
    APPROXIMATE_MATCH = 2
    EXACT_MATCH = 3

class AutomaticExtractor(BaseExtractor):

    def extract(self):
        input_folder = self.configuration.input_folder

        # Find all HTML files inside input folder
        glob_pathname = join(input_folder, '*.html')
        html_files = glob.glob(glob_pathname)

        if len(html_files) < 2:
            raise Exception('Not enough files in input_folder')
        
        with open(html_files[0], 'r+') as first_file:
            with open(html_files[1], 'r+') as second_file:
                wrapper = self.generate_wrapper(first_file.read(), second_file.read())
                return wrapper
    
    @staticmethod
    def clean(html):
        for child in html.children:
            
            # Remove comments
            if isinstance(child, Comment):
                child.extract()
                continue
            
            # Skip all text
            if isinstance(child, NavigableString):
                continue
            
            # Remove the head, script and iframe elements as they don't
            # represent content on page.
            if child.name in ['head', 'script', 'iframe', 'style']:
                child.extract()
                continue
            
            AutomaticExtractor.clean(child)

    @staticmethod
    def mark_optional(element):
        if isinstance(element, NavigableString):
            return
        element['optional'] = True
        element['style'] = 'background: gold'
    
    @staticmethod
    def mark_iterator(element):
        if isinstance(element, NavigableString):
            return
        element['iterator'] = True
        element['style'] = 'background: aqua'
    
    @staticmethod
    def element(el):
        return el.string.strip() if isinstance(el, NavigableString) else el.name

    @staticmethod
    def elements_match(first, second):
        """
            Check if two HTML elements match in tags and attribute names.
        """
        if first.name != second.name: return False

        first_attributes = set(first.attrs.keys())
        second_attributes = set(second.attrs.keys())
        first_attributes.difference_update(['optional', 'iterator', 'style'])
        second_attributes.difference_update(['optional', 'iterator', 'style'])
        return first_attributes == second_attributes

    @staticmethod
    def get_children(node):
        child_filter = lambda element: element != '\n'
        return list(filter(child_filter, node.children))

    @staticmethod
    def accurate_match(wrapper, html):
        """
            Check if wrapper and html elements match in both their tags and at
            least one child.
        """
        if wrapper == html: return Match.EXACT_MATCH
        if isinstance(wrapper, NavigableString) and isinstance(html, NavigableString):
            return Match.EXACT_MATCH
        
        if isinstance(wrapper, NavigableString): return Match.NO_MATCH
        if isinstance(html, NavigableString): return Match.NO_MATCH
        if not AutomaticExtractor.elements_match(wrapper, html): return Match.NO_MATCH

        # Both elements are xml tags and their names do match. Check if their
        # children also match (at least partially).
        wrapper_children = AutomaticExtractor.get_children(wrapper)
        html_children = AutomaticExtractor.get_children(html)

        i = 0
        j = 0

        at_least_one_child_matches = False
        has_optional_elements = False

        # We can assume here that the element tags match. If both trees have no
        # children then they are the same.
        if len(wrapper_children) == 0 and len(html_children) == 0: return Match.EXACT_MATCH

        while i < len(wrapper_children) and j < len(html_children):
            wrapper_element = wrapper_children[i]
            html_element = html_children[j]

            elements_match = AutomaticExtractor.match(wrapper_element, html_element)
            if elements_match:
                i += 1
                j += 1
                at_least_one_child_matches = True
                continue
            
            has_optional_elements = True

            # We have found two children tags that don't match. First, check if
            # the current wrapper_element is optional. Check the current
            # wrapper_element with all remaining children in other document.
            previous_j = j

            while j < len(html_children):
                html_element = html_children[j]
                elements_match = AutomaticExtractor.match(wrapper_element, html_element)
                if elements_match:
                    at_least_one_child_matches = True
                    break
                j += 1
            
            if j >= len(html_children):
                j = previous_j - 1
            
            # Move on to next elements in both trees.
            i += 1
            j += 1
        
        has_optional_elements = has_optional_elements or (i < len(wrapper_children))
        has_optional_elements = has_optional_elements or (j < len(html_children))

        if not at_least_one_child_matches: return Match.NO_MATCH
        if has_optional_elements: return Match.APPROXIMATE_MATCH

        # At least one child matches AND there is no optional elements. This is
        # an exact match.
        return Match.EXACT_MATCH

    @staticmethod
    def match(wrapper, html):
        return AutomaticExtractor.accurate_match(wrapper, html) is not Match.NO_MATCH

    @staticmethod
    def generalize(wrapper, html):
        """
            Try to generalize wrapper element with data from html element. Make
            sure to check if the elements match using AutomaticExtractor.match
            before generalization.
        """
        # The elements are the same object
        if wrapper == html: return True

        # Both elements are strings - if the text doesn't match, then we have
        # discovered a field. Otherwise, we have found a data label.
        if isinstance(wrapper, NavigableString) and isinstance(html, NavigableString):
            if wrapper.string != html.string:
                wrapper.replace_with('#PCDATA')
            return True
        
        # One of the elements is a string and the other is not - the DOM
        # subtrees don't match.
        if isinstance(wrapper, NavigableString): return False
        if isinstance(html, NavigableString): return False

        # Both elements are xml tags, but their names don't match.
        if not AutomaticExtractor.elements_match(wrapper, html): return False

        # Both elements are xml tags and their names do match. Check if their
        # children also match (at least partially).
        wrapper_children = AutomaticExtractor.get_children(wrapper)
        html_children = AutomaticExtractor.get_children(html)

        i = 0
        j = 0

        while i < len(wrapper_children) and j < len(html_children):
            wrapper_element = wrapper_children[i]
            html_element = html_children[j]
            # print(f'Matching: {AutomaticExtractor.element(wrapper_element)} and {AutomaticExtractor.element(html_element)}')

            # Recursively check if the children of the wrapper and other
            # document match. If they do, move on to the next elements in both
            # trees. If not, we have found a tag mismatch and we must perform
            # the search for iterators and / or optionals.
            elements_match = AutomaticExtractor.match(wrapper_element, html_element)
            
            if elements_match:
                AutomaticExtractor.generalize(wrapper_element, html_element)
                wrapper_children = AutomaticExtractor.get_children(wrapper)
                i += 1
                j += 1
                continue

            # We have found two children tags that don't match. First, check if
            # the current wrapper_element is optional. Check the current
            # wrapper_element with all remaining children in other document.
            previous_j = j

            while j < len(html_children):
                html_element = html_children[j]
                elements_match = AutomaticExtractor.match(wrapper_element, html_element)
                if elements_match:
                    break
                j += 1
            
            if j < len(html_children):
                AutomaticExtractor.generalize(wrapper_element, html_element)
                wrapper_children = AutomaticExtractor.get_children(wrapper)

                # The corresponding element has been found in the other
                # document. All elements between previous_j and current j can be
                # marked as optional.
                # Because those elements are not yet in our wrapper, we must
                # copy them into wrapper.
                for k in range(previous_j, j):
                    AutomaticExtractor.mark_optional(html_children[k])
                    # print(f'[j < n] Optional: {html_children[k]}')
                    # print(list(map(AutomaticExtractor.element, wrapper_children)))
                    wrapper_children[i - 1].insert_after(html_children[k])
                    wrapper_children.insert(i, html_children[k])
                    i += 1
            else:
                # The element has not been found. This means that the
                # wrapper_element is optional.
                AutomaticExtractor.mark_optional(wrapper_element)
                # print(f'[j >= n] Optional: {wrapper_element}')
                # print(list(map(AutomaticExtractor.element, wrapper_children)))

                # Reset j to its previous value and try to find the j-th child
                # of html document in wrapper.
                j = previous_j - 1
            
            # Move on to next elements in both trees.
            i += 1
            j += 1
        
        # The loop above might have ended, but not all elements have been
        # matched.
        while i < len(wrapper_children):
            AutomaticExtractor.mark_optional(wrapper_children[i])
            i += 1
        
        while j < len(html_children):
            AutomaticExtractor.mark_optional(html_children[j])

            # Special case - the wrapper has no children, but the other element
            # does. Append the first child and then use a normal version.
            if len(wrapper_children) <= 0:
                wrapper.append(html_children[j])
                wrapper_children = [ html_children[j] ]
            else:
                wrapper_children[i - 1].insert_after(html_children[j])
                wrapper_children.insert(i, html_children[j])
            i += 1
            j += 1
        
        return True
    
    def generate_wrapper(self, first_site, second_site):       
        wrapper_document = BeautifulSoup(first_site, 'html.parser')
        other_document = BeautifulSoup(second_site, 'html.parser')

        # Clean the HTML (in place) - remove script tags, remove page head,
        # scripts, iframes, etc.
        AutomaticExtractor.clean(wrapper_document)
        AutomaticExtractor.clean(other_document)

        # Match the wrapper and another document (in place) and return the
        # modified wrapper.
        AutomaticExtractor.generalize(wrapper_document, other_document)

        print(wrapper_document.prettify())
        return None