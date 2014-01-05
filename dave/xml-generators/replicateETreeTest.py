import xml.etree.ElementTree as ElementTree

def replicateETree(parent, new_parent = None):
    if new_parent == None:
        new_parent = ElementTree.Element(parent.tag, parent.attrib)
        new_parent.text = str(parent.text)
        new_parent.tail = str(parent.tail)
        
    for child in parent:
        new_child = ElementTree.SubElement(new_parent, child.tag, child.attrib)
        new_child.text = str(child.text)
        new_child.tail = str(child.tail)
        replicateETree(child, new_child)

    return new_parent

if __name__ == "__main__":
    xml = ElementTree.parse("sequence_recipe_example.xml")
    print xml
    root_element = xml.getroot()

    new_element = replicateETree(root_element)
    
    print "Old file"
    print ElementTree.tostring(root_element)
    print "Copied file"
    print ElementTree.tostring(new_element)
