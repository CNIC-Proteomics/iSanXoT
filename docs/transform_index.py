# -*- coding: utf-8 -*-
#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
__credits__ = ["Jose Rodriguez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import libraries
import sys
import re

# input files
if len(sys.argv) > 1:
    ifile = sys.argv[1]
    ofile = sys.argv[2]
    # Print the captured arguments
    print("Command line arguments:", sys.argv[1:], flush=True)
else:
    ifile = "index.htm"
    ofile = "index.html"
    print("No command line arguments provided.", flush=True)
    


def main():    
    print("reading files...", flush=True)
    with open(ifile, 'r', encoding='utf8') as file:
        # Read the contents of the file
        content = file.read()
    
    print("adding the new CSS style...", flush=True)
    content = content.replace('</style>',f"{CSS}</style>")
    
    
    print("adding the new LAYERS...", flush=True)
    content = content.replace('<body lang=EN-US link="#2E74B5" vlink="#954F72" style=\'word-wrap:break-word\'>',f"<body lang=EN-US link=\"#2E74B5\" vlink=\"#954F72\" style='word-wrap:break-word'>{LAYER}")
    content = content.replace('</div>\n\n</body>\n\n</html>','</div>\n</div>\n</body>\n</html>')
       
    
    print("removing the first page...", flush=True)
    regex = r"(<div class=WordSection1>).*?(<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>)"
    subst = "<div class=WordSection1>\n<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>"
    content = re.sub(regex, subst, content, 0, re.DOTALL)

    
    # print("moving the table content to sidebar...", flush=True)
    # # extracting the menu from user guide
    # regex = r"<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>\n*<h1>Table of contents</h1>\n*</div>(.*?)<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>"
    # match = re.search(regex, content, re.DOTALL)
    # if match:
    #     extracted_menu = ''
    #     ext_menu = match.group(1)
    #     # remove        
    #     r = r"<p class.*?</p>"
    #     matches = re.finditer(r, ext_menu, re.DOTALL)        
    #     for matchNum, match in enumerate(matches, start=1):            
    #         match_p = match.group()
    #         rr = r"<a href.*?</a>"
    #         match_a = re.search(rr, match_p, re.DOTALL)
    #         if match_a:
    #             match_a = match_a.group()            
    #             # add the "a href" element into ONLY "p" element
    #             # substitute with the capture match 
    #             rrr = r"<p ([^>]*)>.*?</p>"
    #             extracted_menu += re.sub(rrr, rf"<p \1>{match_a}</p>", match_p, 0, re.DOTALL)+'\n'
    #     # remove the menu from user guide
    #     subst = "<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>"
    #     content = re.sub(regex, subst, content, 0, re.DOTALL)
    #     # add the extracted menu to the new user guide
    #     content = content.replace("<div id='sidebar'></div>",f"<div id='sidebar'>{extracted_menu}</div>")
    print("removing the table contents...", flush=True)
    # remove the menu from user guide
    regex = r"<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>\n*<h1>Table of contents</h1>\n*</div>(.*?)<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>"
    subst = "<div style='border:none;border-top:solid windowtext 1.0pt;padding:1.0pt 0in 0in 0in'>"
    content = re.sub(regex, subst, content, 0, re.DOTALL)
        
    
    print("writing output...", flush=True)
    with open(ofile, 'w', encoding='utf8') as file:
        file.write(content)
    
    print("the program has finished succesfully", flush=True)


CSS = '''
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}
#top-menu {
    padding: 5px;
    background-color: black;
    color: #fff;
    text-align: center;
    width: 100%;
    height: 50px;
    position: fixed;
    top: 0;
    z-index: 1000;
}
#logo {
    float: left;
    margin-right: 20px;
    height: 50px;
}
#title {
    font-size: 30px;
    line-height: 30px;
    display: inline-block;
    margin-top: 10px;
}
#sidebar {
    height: 94vh;
    width: 200px;
    position: fixed;
    top: 59px;
    left: 0;
    background-color: #f4f4f4;
	overflow-y: auto;
    z-index: 999;
}
#sidebar a {
    padding-left: 8px;
    text-decoration: none;
    font-size: 14px;
    color: #818181;
    display: block;
}

#sidebar a:hover {
    color: #BF8F00;
}
#sidebar .menu {
    padding: 0;
    margin: 0;
    margin-top: 10px;
    margin-bottom: 20px;
}
#sidebar ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
    margin-bottom: 10px;
}
#sidebar .submenu a {
    padding-left: 20px;
}

#sidebar .submenu2 ul {
    padding-left: 40px;
    list-style-type: square;
}

#main-content {
    padding: 0px 20px 20px 220px;
    top: 59px;
    position: absolute;
}
'''

LAYER = '''
<script>

/* Loop through all dropdown buttons to toggle between hiding and showing its dropdown content - This allows the user to have multiple dropdowns without any conflict */
/*
var dropdown = document.getElementsByClassName("dropdown-btn");
var i;

for (i = 0; i < dropdown.length; i++) {
  dropdown[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var dropdownContent = this.nextElementSibling;
    if (dropdownContent.style.display === "block") {
      dropdownContent.style.display = "none";
    } else {
      dropdownContent.style.display = "block";
    }
  });
}
*/

window.addEventListener('hashchange', offsetAnchor);
window.setTimeout(offsetAnchor, 1);
function offsetAnchor() {
	if (location.hash.length !== 0) {
		window.scrollTo(window.scrollX, window.scrollY - 70);
	}
}

</script>

<div id='top-menu'>
    <img src="images/isanxot/isanxot.png" alt="Logo" id="logo">
    <div id="title">iSanXoT</div>
</div>
<div id='sidebar'>

<ul class='menu'>
  <li><a href="#_Introduction">Introduction</a></li>
  <li><a href="#_License">License</a></li>
  <li class='submenu'><a href="#_Installation">Installation</a>
    <ul>
      <li><a href="#_Download">Download</a></li>
      <li class='submenu2'><a href="#_Available_operating_systems">Available operating systems:</a>
        <ul>
          <li><a href="#_Windows_distribution">Windows distribution</a></li>
          <li><a href="#_MacOS_distribution">MacOS distribution</a></li>
          <li><a href="#_Linux_distribution">Linux distribution</a></li>
        </ul>
      </li>
    </ul>
  <li><a href="#_Get_Started">Getting Started</a></li>
  <li class='submenu'><a href="#_Modules">Modules</a>
    <ul>
      <li class='submenu2'><a href="#_RELS_CREATOR">Relation Tables Module:</a>
        <ul>
          <li><a href="#_RELS_CREATOR">RELS CREATOR</a></li>
        </ul>
      </li>
      <li class='submenu2'><a href="#_Basic_modules">Basic Modules:</a>
        <ul>
          <li><a href="#_LEVEL_CREATOR">LEVEL CREATOR</a></li>
          <li><a href="#_LEVEL_CALIBRATOR">LEVEL CALIBRATOR</a></li>
          <li><a href="#_INTEGRATE">INTEGRATE</a></li>
          <li><a href="#_NORCOMBINE">NORCOMBINE</a></li>
          <li><a href="#_RATIOS">RATIOS</a></li>
          <li><a href="#_SBT">SBT</a></li>
        </ul>
      </li>
      <li class='submenu2'><a href="#_Compound_modules">Compound Modules:</a>
        <ul>
          <li><a href="#_WSPP-SBT_1">WSPP-SBT</a></li>
          <li><a href="#_WSPPG-SBT_1">WSPPG-SBT</a></li>
          <li><a href="#_WPP-SBT_1">WPP-SBT</a></li>
          <li><a href="#_WPPG-SBT_1">WPPG-SBT</a></li>
        </ul>
      </li>
      <li class='submenu2'><a href="#_Report_modules">Report Modules:</a>
        <ul>
          <li><a href="#_REPORT">REPORT</a></li>
          <li><a href="#_SANSON">SANSON</a></li>
        </ul>
      </li>
      <li class='submenu2'><a href="#_Special_parameters">Special parameters:</a>
        <ul>
          <li><a href="#_Multiple_samples">Multiple samples</a></li>
          <li><a href="#_Asterisk_is_our">Multiple samples in the inputs and outputs</a></li>
          <li><a href="#_Multiple_samples_in">INTEGRATE</a></li>
          <li><a href="#_More_params">More params</a></li>
          <li><a href="#_Filter_param_(in">Filter (for REPORT and SANSON)</a></li>
        </ul>
      </li>
    </ul>
  </li>
  <li class='submenu2'><a href="#_Sample_Workflows_with">Sample Workflows:</a>
    <ul>
      <li><a href="#_Workflow_1:_One-step">Wkf 1: One-step quantification</a></li>
      <li><a href="#_Workflow_2:_Step-by-step">Wkf 2: Step-by-step quantification and sample combination</a></li>
      <li><a href="#_Workflow_3:_Quantification">Wkf 3: PTMs quantification</a></li>
      <li><a href="#_Workflow_4:_Label-free">Wkf 4: Label-free quantification</a></li>
    </ul>
  </li>
  <li><a href="#_Toc152521038">Importing a workflow template</a></li>
  <li class='submenu2'><a href="#_Creating_the_identification/quantif">Creating the ID-q file from </a>
    <ul>
      <li><a href="#_Toc152521040">Proteome Discoverer</a>
      <li><a href="#_Toc152521043">MaxQuant</a>
      <li><a href="#_Toc124328462">FragPipe</a>
    </ul>
  </li>
  <li><a href="#_Toc152521049">Adapting the results from proteomics pipelines for iSanXoT</a></li>
  <li><a href="#_References">References</a></li>
</ul>


</div>
</div>
<div id='main-content'>
'''

# Check if the script is being run as the main module
if __name__ == "__main__":
    # Call the main function
    main()