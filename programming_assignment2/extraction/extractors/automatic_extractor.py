from .base_extractor import BaseExtractor
from bs4 import BeautifulSoup, NavigableString
from os.path import join
import glob

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
            
            # Skip all text
            if isinstance(child, NavigableString):
                continue
            
            # Remove the head, script and iframe elements as they don't
            # represent content on page.
            if child.name in ['head', 'script', 'iframe', 'style']:
                child.extract()
            
            AutomaticExtractor.clean(child)

    @staticmethod
    def mark_optional(element):
        if isinstance(element, NavigableString):
            return
        element['optional'] = True
        element['style'] = 'border: 1px solid red'
    
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
        return first_attributes == second_attributes

    @staticmethod
    def tree_matching(wrapper, html):
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
        newline_filter = lambda element: element != '\n'
        wrapper_children = list(filter(newline_filter, wrapper.children))
        html_children = list(filter(newline_filter, html.children))

        # m = len(wrapper_children)
        # n = len(html_children)

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
            elements_match = AutomaticExtractor.tree_matching(wrapper_element, html_element)
            
            if elements_match:
                i += 1
                j += 1
                continue
            
            match_found = False

            # We have found two children tags that don't match. First, check if
            # the current wrapper_element is optional. Check the current
            # wrapper_element with all remaining children in other document.
            previous_j = j

            while j < len(html_children):
                html_element = html_children[j]
                if AutomaticExtractor.tree_matching(wrapper_element, html_element):
                    break
                j += 1
            
            if j < len(html_children):
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

                match_found = True
            else:
                # The element has not been found. This means that the
                # wrapper_element is optional.
                AutomaticExtractor.mark_optional(wrapper_element)
                # print(f'[j >= n] Optional: {wrapper_element}')
                # print(list(map(AutomaticExtractor.element, wrapper_children)))

                # Reset j to its previous value and try to find the j-th child
                # of html document in wrapper.
                j = previous_j
            
            # If the wrapper element could not be matched to any element inside
            # the html, we must search for html_element inside the wrapper.
            if not match_found:
                previous_i = i
                html_element = html_children[j]

                while i < len(wrapper_children):
                    wrapper_element = wrapper_children[i]
                    if AutomaticExtractor.tree_matching(wrapper_element, html_element):
                        break
                    i += 1
                
                if i < len(wrapper_children):
                    # The match for html_element has been found inside wrapper.
                    # We must mark all items between previous_i and current i as
                    # optional.
                    for k in range(previous_i, i):
                        AutomaticExtractor.mark_optional(wrapper_children[k])
                        # print(f'[i < m] Optional: {wrapper_children[k]}')
                        # print(list(map(AutomaticExtractor.element, wrapper_children)))

                    # Beacuse the optional elements are already in wraper, no
                    # further work is required here.
                else:
                    # The html_element has no match in wrapper. This means that
                    # is an optional element. We must copy it into our wrapper.
                    i = previous_i

                    AutomaticExtractor.mark_optional(html_children[j])
                    wrapper_children[i].insert_after(html_children[j])
                    wrapper_children.insert(i, html_children[j])
                    # print(f'[i >= m] Optional: {html_children[j]}')
                    # print(list(map(AutomaticExtractor.element, wrapper_children)))
                    i += 1

                    # AutomaticExtractor.mark_optional(html_children[j])
                    # wrapper_children[i].insert_after(html_children[j])
            
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
        AutomaticExtractor.tree_matching(wrapper_document, other_document)

        print(wrapper_document.prettify())
        return None