#!/usr/bin/python

import sys, os, operator 
from pprint import pprint
from tikz_dependency import *
from dependency_graph import *
from conll_analysis_output import *

DEBUG = False

# The directory containing the original conll data file
CONLL_DIR = "data/"
CONLL_LOC = CONLL_DIR+"english_ptb_train.conll"
if len(sys.argv) > 2:
    CONLL_LOC = sys.argv[2]
if not os.path.exists(CONLL_DIR):
    os.makedirs(CONLL_DIR)

# The directory containing our link-conll result data file
SOL_DIR = "sol/"
SOL_LOC = SOL_DIR+"links.conll"
if not os.path.exists(SOL_DIR):
    os.makedirs(SOL_DIR)

# Analysis directory and files. Where we will store these results.
ANALYSIS_DIR = "sol/conll_analysis/"
ANALYSIS_FILE = ANALYSIS_DIR+"conll_analysis.txt"
if not os.path.exists(ANALYSIS_DIR):
    os.makedirs(ANALYSIS_DIR)

# The trial number. How many sentences we take in originally.
TRIAL_NUM = 0
if len(sys.argv) > 3:
    TRIAL_NUM = int(sys.argv[3])

# Latex directory and files. Where we will store these results in latex form.
LATEX_DIR = "doc/figure/"
LATEX_FILE_SENTENCE = LATEX_DIR+"conll_analysis_sentences.tex"
LATEX_FILE_SENTENCE_DISCONNECTED = LATEX_DIR+"conll_analysis_sentences_disconnected.tex"
LATEX_FILE_SENTENCE_DROPPED = LATEX_DIR+"conll_analysis_sentences_dropped.tex"
LATEX_FILE_SENTENCE_MULTIHEADED = LATEX_DIR+"conll_analysis_sentences_multiheaded.tex"
LATEX_FILE_SENTENCE_TOTAL = LATEX_DIR+"conll_analysis_sentences_total.tex"
LATEX_FILE_SENTENCE_ORIGINAL = LATEX_DIR+"conll_analysis_sentences_original.tex"
LATEX_FILE_ARCS = LATEX_DIR+"conll_analysis_arcs.tex"
LATEX_FILE_CONLL_RECALL = LATEX_DIR+"conll_analysis_recall.tex"
LATEX_FILE_CONLL_PRECISION = LATEX_DIR+"conll_analysis_precision.tex"
LATEX_FILE_EDGE_PERCENT = LATEX_DIR+"conll_analysis_edge_percent.tex"


if not os.path.exists(LATEX_DIR):
    os.makedirs(LATEX_DIR)

# Tikz directory and files
TIKZ_DIR = "doc/figure/"
if not os.path.exists(TIKZ_DIR):
    os.makedirs(TIKZ_DIR)
EXAMPLE_SENTENCES_LOC = TIKZ_DIR+"sentences.tikz"
PAPER_TIKZ = open(EXAMPLE_SENTENCES_LOC, 'w+')

EXAMPLE_PARSES_LOC = TIKZ_DIR+"parses.tikz"
EXAMPLE_PARSES = open(EXAMPLE_PARSES_LOC, 'w+')

LONG_EXAMPLE_SENTENCES_LOC = TIKZ_DIR+"long_parses.tikz"
LONG_EXAMPLE_PARSES = open(LONG_EXAMPLE_SENTENCES_LOC, 'w+')

LONG_EXAMPLE_SENTENCES2_LOC = TIKZ_DIR+"long_parse2.tikz"
LONG_EXAMPLE_PARSES2 = open(LONG_EXAMPLE_SENTENCES2_LOC, 'w+')



ALLOWED_LABELS = SOL_DIR + "allowedLinks.txt"
ALLOWED_LABELS = open(ALLOWED_LABELS, "r")
ALLOWED_LABELS_BOTH = LATEX_DIR+"allowed_labels_both.tex"
ALLOWED_LABELS_TOTAL = LATEX_DIR+"allowed_labels_total.tex"

LABEL_TOKEN_DISALLOWED = LATEX_DIR+"label_token_disallowed.tex"
LABEL_TOKEN_TOTAL = LATEX_DIR+"label_token_total.tex"


allowedLabel = {}
ALLOWED_LABELS = ALLOWED_LABELS.readlines()
for line in ALLOWED_LABELS:
    line = line.split()
    if not line:
        continue

    label = line[0]
    direction = line[1]
    allowedLabel[label] = allowedLabel.get(label,{})
    allowedLabel[label][direction] = True


bothCount = 0
for label in allowedLabel:
    dirs = allowedLabel[label]
    if len(dirs) > 1:
        bothCount += 1

f = open(ALLOWED_LABELS_BOTH,"w+")
f.write(str(bothCount))
f.close()

f = open(ALLOWED_LABELS_TOTAL,"w+")
f.write(str(len(allowedLabel)))
f.close()






# --------------------------------------------------------------------
# Analysis while reading in data. Pertains mostly to sentence counts
# --------------------------------------------------------------------
# Number of sentences from the link data
link_sentence_total = 0
link_dropped_sentences = 0
link_remaining_sentences = 0

# These maps will map a sentence to its conll representation.
# We will use this to query conll results from both our conll and link-conll files
conll_results = {}
link_results = {}



# Analysis
def analysis(conlls, links):
    word_data = analysis_words(conlls, links)
    
    graph_conlls = getGraph(conlls)
    graph_links = getGraph(links)

    matches = []
    reverse_matches = []
    extras = []

    label_match = {}
    label_match_count = {}

    label_reverse = {}
    label_reverse_count = {}

    label_extra = {}
    label_extra_count = {}
    
    mismatches = 0
    #blanks = 0
    total = 0
    
    for head in graph_conlls.table:
        children = graph_conlls.table[head]
        total += len(children)

        for child in children:
            conll_label = graph_conlls.getEdge(head,child)

            # If we have a match
            if graph_links.existsEdge(head,child):
                matches.append((head,child))
                link_label = graph_links.getEdge(head,child)
                
                label_match[conll_label] = label_match.get(conll_label, set([])).union(set([link_label]))
                label_match_count[(conll_label, link_label)] = label_match_count.get((conll_label, link_label),0) + 1

            # If we have a reverse match
            elif graph_links.existsEdge(child,head):
                reverse_matches.append((child,head))
                link_label = graph_links.getEdge(child,head)
                
                label_reverse[conll_label] = label_reverse.get(conll_label, set([])).union(set([link_label]))
                label_reverse_count[(conll_label, link_label)] = label_reverse_count.get((conll_label, link_label), 0) + 1

            # We have a mismatch
            else:
                mismatches += 1
                if not graph_links.heads.get(child,[]):
                    blanks +=1

    # Delete the matches from the graphs, so we can work with the rest
    for match in matches:
        (head,child) = match
        graph_conlls.deleteEdge(head,child)
        graph_links.deleteEdge(head,child)

    # Delete the reverse matches from the graphs, so wecan work with the rest
    for reverse in reverse_matches:
        (child,head) = reverse
        graph_conlls.deleteEdge(head,child)
        graph_links.deleteEdge(child,head)
    
    # Find the extra links
    for head in graph_links.table:
        children = graph_links.table[head]
        
        for child in children:
            if len(graph_links.heads[child]) > 1:
                extras.append((head,child))
                link_label = graph_links.getEdge(head,child)

                label_extra[link_label] = label_extra.get(link_label, set([])).union(set([link_label]))
                label_extra_count[link_label] = label_extra_count.get(link_label,0) + 1

    # Delete the extras from link graph, so we can work with the rest
    for extra in extras:
        (head, child) = extra
        graph_links.deleteEdge(head,child)

    matches = len(matches)
    reverse_matches = len(reverse_matches)
    extras = len(extras)

    match_data = (matches, label_match, label_match_count)
    reverse_data = (reverse_matches, label_reverse, label_reverse_count)    
    extra_data = (extras, label_extra, label_extra_count)
    mismatch_data = (mismatches)

    return (match_data, reverse_data, extra_data, word_data, mismatch_data, total)


# Counts the word tokens that are multiheaded or dropped. Compared with the total number of word tokens
def analysis_words(conlls,links):
    word_count = 0
    
    multiheaded_count = 0
    isMultiheaded = False
    #dropped_word_count = 0        
    #hasDropped = False
    
    word_count += len(links)
    for conll,link in zip(conlls,links):
        link = link.split()
        """
        if link[6] == "-":
            dropped_word_count += 1
            hasDropped = True
        """

        link_heads = link[6].split(",")

        if len(link_heads) > 1:
            multiheaded_count += 1
            isMultiheaded = True

    multiheaded_data = (multiheaded_count, isMultiheaded)
    #dropped_data = (dropped_word_count, hasDropped)
    #return (dropped_data, multiheaded_data, word_count)
    return (multiheaded_data, word_count)




# Analysis on the links. For the appendix of the paper
def analysis_links(links):
    link_direction_counts = {}
    link_label_multiheaded = {}

    for link in links:
        link = link.split()
        index = int(link[0])
        heads = link[6].split(",")
        labels = link[7].split(",")
        
        if len(heads) > 1:
            for label in labels:
                coarse_label = get_coarse_label(label)

                link_label_multiheaded[coarse_label] = link_label_multiheaded.get(coarse_label, 0) + 1


        for (head,label) in zip(heads,labels):
            head = int(head)

            link_direction_counts[label] = link_direction_counts.get(label,{})
            if head < index:
                link_direction_counts[label]["right"] = link_direction_counts[label].get("right",0) + 1
            elif head > index:
                link_direction_counts[label]["left"] = link_direction_counts[label].get("left",0) + 1


    return (link_direction_counts, link_label_multiheaded)



# Gets the coarse label for any given specific label
def get_coarse_label(label):
    coarse_label = "".join(w for w in list(label) if w.isupper())    
    if len(list(coarse_label)) >= 2 and list(coarse_label)[0] == "I" and list(coarse_label)[1] == "D":
        coarse_label = "ID"
    return coarse_label





# Populating the link_results
f = open(SOL_LOC)
f = f.readlines()
sentence = []
conll = []

skipSentence = False
for line in f:
    line = line.strip()

    if not line:
        if skipSentence:
            link_dropped_sentences += 1
            skipSentence = False
        else:
            if "RIGHT-WALL" in sentence:
                sentence = sentence[:-1]

            # The sentence is stored as lower case.
            ID = " ".join(sentence)
            ID = ID.lower()
            link_results[ID] = tuple(conll)


        
        sentence = []
        conll = []
        link_sentence_total += 1
    else:
        conll.append(line)
        word = line.split()[1]

        if word.rfind("[") != -1 and word.rfind("]") != -1 and word.rfind("[!]") == -1:
            skipSentence = True


        # Remove the [!] at the end of words that link parser could not recognize
        index = -1
        index = word.rfind("[!]")
        if index != -1:
            word = word[:(index)]

        """index = -1
        index = word.rfind("[?]")
        if index != -1:
            word = word[:index]+word[index+len("[?]"):]
        print word"""



        # Get rid of the [] brackets around words that the link-parser could not attach.        
        #word = word.strip("[]")
        sentence.append(word)


link_remaining_sentences = link_sentence_total - link_dropped_sentences
if DEBUG:
    print "link_sentence_total", link_sentence_total
    print "link_dropped_sentences", link_dropped_sentences
    print "link_remaining_sentences", link_remaining_sentences
    print "percent dropped sentences", float(link_dropped_sentences) / link_sentence_total
    print "percent remaining sentences", float(link_remaining_sentences) / link_sentence_total
    print


# Populating the conll_results
f = open(CONLL_LOC)
f = f.readlines()
sentence = []
conll = []



for line in f:
    line = line.strip()

    if not line:
        # The sentence is stored as lower case, because link-parser will sometimes lowercase the words that it does not know.
        ID = " ".join(sentence)
        ID = ID.lower()
        


        # Check to see if the sentence is in the link data. 
        # This is a small optimization. We don't need to store all of the conll data. 
        if ID in link_results:
            conll_results[ID] = tuple(conll)

        sentence = []
        conll = []
    else:
        conll.append(line)
        word = line.split()[1]
        sentence.append(word)

        

# --------------------------------------------------------------------
# Variables for the link analysis
# --------------------------------------------------------------------
arc_total = 0

match_total = 0
all_matches = {}
all_match_counts = {}

extra_total = 0
all_extra_counts = {}

#blank_total = 0
#all_blank_counts = {}

mismatch_total = 0
reverse_match_total = 0
mismatch_directionality = {}
mismatch_directionality_counts = {}

#mismatch_extra_total = 0
#mismatch_extra_counts = {}

link_direction_totals = {}
link_direction_coarse_totals = {}
link_label_isMultiheaded = {}

# --------------------------------------------------------------------
# Variables for word analysis
# --------------------------------------------------------------------
multiheaded_word_count = 0
dropped_word_total = 0
word_count_total = 0

multiheaded_sentence_count = 0


# --------------------------------------------------------------------
# Variables for the sentences used in the tikz output
# --------------------------------------------------------------------
paper_sentence_count = 0
paper_sentence_skip = 0
paper_sentence_limit = 2

example_parses_count = 0
example_parses_skip = 0
example_parses_limit = 100

long_example_parses_count = 0
long_example_parses_skip = 90
long_example_parses_limit = 1

long_example_parses2_count = 0
long_example_parses2_skip = 0
long_example_parses2_limit = 0


for linkSentence in link_results:
    if linkSentence not in conll_results:
        continue


    # Remove sentences with [!] or [?] in them. I will have them later in the paper and explain what it means.
    sentenceCheck = True
    for line in link_results[linkSentence]:
        line = line.split()
        word = line[1]
        if word.rfind("[!]") != -1 or word.rfind("[?]") != -1:
            sentenceCheck = False
            
    # I am preventing certain sentences from appearing in the paper.
    # I just wanted to skip over some sentences because they didn't look cool enough
    #bannedWords = ["salees", "soldiers", "word", "serwer", "reason"]
    bannedWords = ["consensus", ":"]
    for word in bannedWords:
        if word in linkSentence:
            sentenceCheck = False
            break
    


    tempSentence = [] 
    linkData = link_results[linkSentence]
    for line in linkData:
        line = line.split("\t")
        tempSentence.append(line[1])
    tempSentence = " ".join(tempSentence)
    sentenceLength = len(tempSentence)



    # Link parses to put in the paper. Takes sentences of only length 5.
    if (paper_sentence_count < paper_sentence_limit) and sentenceLength >= 45 and sentenceLength <= 45 and sentenceCheck:
        if paper_sentence_skip > 0:
            paper_sentence_skip -= 1
        else:
            tikz = tikz_dependency(conll_results[linkSentence], link_results[linkSentence], linkSentence, .97 / 2)      
            PAPER_TIKZ.write(tikz)
            paper_sentence_count += 1
            if paper_sentence_count % 2 == 0:
                PAPER_TIKZ.write("\n")
    elif long_example_parses_count < long_example_parses_limit and sentenceLength >= 85 and sentenceLength <= 90 and sentenceCheck:
        if long_example_parses_skip > 0:
            long_example_parses_skip -= 1
        else:
            tikz = tikz_dependency(conll_results[linkSentence], link_results[linkSentence], linkSentence, .97)

            #LONG_EXAMPLE_PARSES.write("\\begin{figure*}[ht!]\n")
            LONG_EXAMPLE_PARSES.write(tikz)
            #LONG_EXAMPLE_PARSES.write("\\end{figure*}\n\n")
            long_example_parses_count += 1
            #if long_example_parses_count % 1 == 0:
            LONG_EXAMPLE_PARSES.write("\n")



    elif long_example_parses2_count < long_example_parses2_limit and sentenceLength >= 90 and sentenceLength <= 90 and sentenceCheck:
        if long_example_parses2_skip > 0:
            long_example_parses2_skip -= 1
        else:
            tikz = tikz_dependency(conll_results[linkSentence], link_results[linkSentence], linkSentence, .97)
            #LONG_EXAMPLE_PARSES2.write("\\begin{figure*}[ht!]\n")
            LONG_EXAMPLE_PARSES2.write(tikz)
            #LONG_EXAMPLE_PARSES2.write("\\end{figure*}\n\n")
            long_example_parses2_count += 1
            #if long_example_parses2_count % 1 == 0:
            LONG_EXAMPLE_PARSES2.write("\n")
    

            
    # Filter out sentences to only up to length 16
    elif example_parses_count < example_parses_limit and sentenceLength <= 95:
    #elif example_parses_count < example_parses_limit and sentenceLength >= 85 and sentenceLength <= 90 and sentenceCheck:
        if example_parses_skip > 0:
            example_parses_skip -= 1

        else:
            #elif example_parses_count < example_parses_limit:
            tikz = tikz_dependency(conll_results[linkSentence], link_results[linkSentence], linkSentence, 1.0, False)
            EXAMPLE_PARSES.write("\\begin{figure*}[ht!]\n")
            EXAMPLE_PARSES.write(tikz)
            EXAMPLE_PARSES.write("\\end{figure*}\n\n")
            example_parses_count += 1
            if example_parses_count % 18 == 0:
                EXAMPLE_PARSES.write("\clearpage")


    # analysis_links
    (link_direction_counts, link_label_multiheaded) = analysis_links(link_results[linkSentence])
    for label in link_direction_counts:
        coarse_label = get_coarse_label(label)

        link_direction_coarse_totals[coarse_label] = link_direction_coarse_totals.get(coarse_label,{})
        link_direction_totals[label] = link_direction_totals.get(label,{})

        for direction in link_direction_counts[label]:
            link_direction_totals[label][direction] = link_direction_totals[label].get(direction, 0) + link_direction_counts[label][direction]
            link_direction_coarse_totals[coarse_label][direction] = link_direction_coarse_totals[coarse_label].get(direction,0) + link_direction_counts[label][direction]

    for coarse_label in link_label_multiheaded:
        link_label_isMultiheaded[coarse_label] = link_label_isMultiheaded.get(coarse_label,0) + link_label_multiheaded[coarse_label]




    (match_data, reverse_data, extra_data, word_data, mismatch_data, total) = analysis(conll_results[linkSentence], link_results[linkSentence])

    (matches, label_match, label_match_count)                           = match_data
    (reverse_matches, label_reverse, label_reverse_count)               = reverse_data
    (extras, label_extra, label_extra_count)                            = extra_data

    (mismatches)                                                = mismatch_data 
    (multiheaded_data, word_count)                        = word_data

    #(dropped_word_count, hasDropped)                                    = dropped_data
    (multiheaded_count, isMultiheaded)                                  = multiheaded_data

    match_total += matches
    #blank_total += blanks
    reverse_match_total += reverse_matches
    mismatch_total += mismatches

    extra_total += extras
    arc_total += total

    multiheaded_word_count += multiheaded_count
    #dropped_word_total += dropped_word_count
    word_count_total += word_count

    if isMultiheaded:
        multiheaded_sentence_count += 1 

    for label in label_match:
        all_matches[label] = all_matches.get(label,set([])).union(label_match[label])
    for pair in label_match_count:
        all_match_counts[pair] = all_match_counts.get(pair,0) + label_match_count[pair]

    for label in label_extra_count:
        all_extra_counts[label] = all_extra_counts.get(label, 0) + label_extra_count[label]

    for label in label_reverse:
        mismatch_directionality[label] = mismatch_directionality.get(label, set([])).union(label_reverse[label])

    for pair in label_reverse_count:
        mismatch_directionality_counts[pair] = mismatch_directionality_counts.get(pair,0) + label_reverse_count[pair]



f = open(ANALYSIS_FILE, "w+")
result = result_numbers(arc_total, 
                        match_total, 
                        extra_total, 
                        #blank_total, 
                        mismatch_total, 
                        reverse_match_total, 
                        #mismatch_extra_total, 
                        #dropped_word_total,
                        multiheaded_word_count, 
                        word_count_total, 
                        link_dropped_sentences,
                        multiheaded_sentence_count, 
                        TRIAL_NUM,
                        link_sentence_total,
                        link_remaining_sentences)
                        

f.write(result)
f.close()



result = result_latex_corpus(TRIAL_NUM, 
                             link_sentence_total, 
                             link_remaining_sentences)
f = open(LATEX_FILE_SENTENCE, "w+")
f.write(result)
f.close()

result = result_latex_arcs(match_total, reverse_match_total, mismatch_total, arc_total)
f = open(LATEX_FILE_ARCS, "w+")
f.write(result)
f.close()








#---------------------------------------------------------------------
# Take our generated numbers and put them in latex files 
# to be called by the paper
#---------------------------------------------------------------------
disconnected_sentence_percentage = "{:.2f}".format(float(TRIAL_NUM - link_sentence_total) / TRIAL_NUM * 100)+"\\%"
dropped_sentence_percentage = "{:.2f}".format(float(link_dropped_sentences) / link_sentence_total * 100)+"\\%"
multiheaded_sentence_percentage = float(multiheaded_sentence_count) / link_remaining_sentences * 100
multiheaded_sentence_percentage = "{:.2f}".format(multiheaded_sentence_percentage)+"\\%"
f = open(LATEX_FILE_SENTENCE_DISCONNECTED, "w+")
f.write(disconnected_sentence_percentage)
f.close()

f = open(LATEX_FILE_SENTENCE_DROPPED, "w+")
f.write(dropped_sentence_percentage)
f.close()

f = open(LATEX_FILE_SENTENCE_MULTIHEADED, "w+")
f.write(multiheaded_sentence_percentage)
f.close()

f = open(LATEX_FILE_SENTENCE_TOTAL, "w+")
f.write("{:,d}".format(link_sentence_total))
f.close()

f = open(LATEX_FILE_SENTENCE_ORIGINAL, "w+")
f.write("{:,d}".format(TRIAL_NUM))
f.close()

#print result


#print "ALL MATCH COUNTS"
#pprint(all_match_counts)
#print

#print "MISMATCH DIRECTIONALITY COUNTS"
#pprint(mismatch_directionality_counts)
#print






#---------------------------------------------------------------------
# Setting up the matching link label counts and majority predictions
# This will be used in a table of the appendix of the paper
#---------------------------------------------------------------------
link_label_prediction = {}
link_label_coarse_prediction = {}
coarse_dir_mismatch = {}
for (label_conll, label_link) in all_match_counts:
    link_label_prediction[label_link] = link_label_prediction.get(label_link, {})
    link_label_prediction[label_link][label_conll] = link_label_prediction[label_link].get(label_conll, 0)
    link_label_prediction[label_link][label_conll] += all_match_counts[(label_conll, label_link)]

    coarse_label_link = get_coarse_label(label_link)
    link_label_coarse_prediction[coarse_label_link] = link_label_coarse_prediction.get(coarse_label_link,{})
    link_label_coarse_prediction[coarse_label_link][label_conll] = link_label_coarse_prediction[coarse_label_link].get(label_conll,0)
    link_label_coarse_prediction[coarse_label_link][label_conll] += all_match_counts[(label_conll, label_link)]


for (label_conll, label_link) in mismatch_directionality_counts:
    link_label_prediction[label_link] = link_label_prediction.get(label_link, {})
    link_label_prediction[label_link][label_conll] = link_label_prediction[label_link].get(label_conll, 0)
    link_label_prediction[label_link][label_conll] += mismatch_directionality_counts[(label_conll, label_link)]

    coarse_label_link = "".join(w for w in list(label_link) if w.isupper())
    link_label_coarse_prediction[coarse_label_link] = link_label_coarse_prediction.get(coarse_label_link,{})
    link_label_coarse_prediction[coarse_label_link][label_conll] = link_label_coarse_prediction[coarse_label_link].get(label_conll,0)
    link_label_coarse_prediction[coarse_label_link][label_conll] += mismatch_directionality_counts[(label_conll, label_link)]
    
    coarse_dir_mismatch[coarse_label_link] = coarse_dir_mismatch.get(coarse_label_link,0)
    coarse_dir_mismatch[coarse_label_link] += mismatch_directionality_counts[(label_conll, label_link)]


#pprint(coarse_dir_mismatch)

#pprint(link_label_coarse_prediction)    




# Gives us total counts. The normalizing constants to use later.
link_label_prediction_totals = {}
for label in link_label_prediction:
    conlls = link_label_prediction[label]
    count = 0
    for conll in conlls:
        count += conlls[conll]
    link_label_prediction_totals[label] = count

predictions = {}
for label_link in link_label_prediction:
    conll_map = link_label_prediction[label_link]
    predictions[label_link] = max(conll_map.iteritems(), key=operator.itemgetter(1))[0]


link_label_coarse_prediction_totals = {}
for label in link_label_coarse_prediction:
    conlls = link_label_coarse_prediction[label]
    count = 0
    for conll in conlls:
        count += conlls[conll]
    link_label_coarse_prediction_totals[label] = count

coarse_predictions = {}
for label_link in link_label_coarse_prediction:
    conll_map = link_label_coarse_prediction[label_link]
    coarse_predictions[label_link] = max(conll_map.iteritems(), key=operator.itemgetter(1))[0]


#pprint(predictions)
#pprint(link_label_prediction)
#pprint(link_label_coarse_prediction)
#pprint(coarse_predictions)


#---------------------------------------------------------------------
# Setting up Link label counts 
# which is used for a table in the appendix of the paper
#---------------------------------------------------------------------
#pprint(link_direction_totals)
#pprint(link_direction_coarse_totals)

link_label_counts = {}
for label in link_direction_totals:
    count = 0
    for direction in link_direction_totals[label]:
        count += link_direction_totals[label][direction]
    link_label_counts[label] = count
labels = link_label_counts.keys()
labels.sort()

link_label_coarse_counts = {}
for label in link_direction_coarse_totals:
    count = 0
    for direction in link_direction_coarse_totals[label]:
        count += link_direction_coarse_totals[label][direction]
    link_label_coarse_counts[label] = count
coarse_labels = link_label_coarse_counts.keys()
coarse_labels.sort()

#---------------------------------------------------------------------
# Analysis/counts of the links, their labels, and their directions
# For the appendix section of the paper
#---------------------------------------------------------------------
LATEX_FILE_LINKS = LATEX_DIR+"link_analysis_table.tex"
f = open(LATEX_FILE_LINKS, "w+")
latex_table = "\\begin{tabular}{|l|l|l|l||l|l|}\n"
header = "Label & Count & Left & Right & CoNLL & CoNLL Percentage\\\\ \n"

begin_figure = "\\begin{figure*}\n"
end_figure = "\\end{figure*}\n"

table = begin_figure
table += latex_table
table += "\\hline\n"
table += header
line = 0
for label in labels:
    count = link_label_counts[label]
    
    left = link_direction_totals[label].get("left",0)
    left = str(int(float(left) / count * 100))+"\\%" + " ("+str(left)+")"
    right = link_direction_totals[label].get("right",0)
    right = str(int(float(right) / count * 100))+"\\%" + " ("+str(right)+")"

    prediction = predictions.get(label, "-")
    prediction_num = ""
    prediction_total = ""
    prediction_percent = ""
    if prediction != "-":
        prediction_num = link_label_prediction[label][prediction]
        prediction_total = link_label_prediction_totals[label]
    if prediction_num and prediction_total:
        prediction_percent = str(int(float(prediction_num) / prediction_total * 100 + 0.5)) + "\\%" + " (" + str(prediction_num) + "/" + str(prediction_total) + ")"


    table += "\\hline\n"
    table += " "+label+" & "+str(count)+" & "+left+" & "+right+" & "+prediction+" & "+prediction_percent+" \\\\ \n"
    line += 1
    
    # Break up the table into smaller tables
    if line % 50 == 0:
        table += "\\hline\n"
        table += "\\end{tabular}\n"
        table += end_figure
        table += begin_figure
        table += latex_table
        table += "\\hline\n"
        table += header
    
table += "\\hline\n"
table += "\\end{tabular}\n"
table += end_figure

f.write(table)
f.close()





#---------------------------------------------------------------------
# Coarse analysis/counts of the links, their labels, and their directions
# For the appendix section of the paper
#---------------------------------------------------------------------
LATEX_FILE_COARSE_LINKS = LATEX_DIR+"link_analysis_coarse_table.tex"
f = open(LATEX_FILE_COARSE_LINKS, "w+")


# TODO use tabular
latex_table = "\\begin{longtable}{|l|l|l|l|l|l|}\n\\hline\n"
end_table = "\\end{longtable}\n"

header = "Label & Rightward & Multiheaded & CoNLL Match & CoNLL Dir Match & CoNLL Label\\\\"

begin_figure = "\\begin{small}\n\\centering\n"
end_figure = "\\end{small}\n"

def make_percentage_figure(top,bottom):
    return str(int(float(top) / float(bottom) * 100 + 0.5))+"\\%" + " ("+str(top)+"/"+str(bottom)+")"


table = begin_figure
table += latex_table

table += header + "\\hline\n"
table += "\\endhead\n"
table += "\n"

table += "\\hline\n\\endfoot\n\n"

line = 0
for coarse_label in coarse_labels:
    count = link_label_coarse_counts[coarse_label]
    
    right = link_direction_coarse_totals[coarse_label].get("right",0)
    right = make_percentage_figure(right,count)

    prediction_num = ""
    prediction_total = ""
    match_percent = ""
    mismatch_percent = ""
    multiheaded = make_percentage_figure(link_label_isMultiheaded.get(coarse_label,0), count)


    prediction = coarse_predictions.get(coarse_label, "-")
    if prediction != "-":
        prediction_num = link_label_coarse_prediction[coarse_label][prediction]
        prediction_total = link_label_coarse_prediction_totals[coarse_label]
        prediction += " "+ make_percentage_figure(prediction_num, prediction_total)
        

    if prediction_num and prediction_total:
        match_percent = make_percentage_figure(prediction_total, count)

        mismatch_percent = make_percentage_figure((prediction_total - coarse_dir_mismatch.get(coarse_label,0)), prediction_total)


    else:
        match_percent = "-"
        mismatch_percent = "-"

    #table += "\\hline\n"
    table += coarse_label
    table += " & "+right
    table += " & "+multiheaded
    table += " & "+match_percent
    table += " & "+mismatch_percent
    table += " & "+prediction
    table += " \\\\ \n"
    line += 1
    
    # Break up the table into smaller tables
    """if line % 55 == 0:
        table += "\\hline\n"
        table += end_table
        table += end_figure
        table += begin_figure
        table += latex_table
        table += "\\hline\n"
        table += header
    """
#table += "\\hline\n"
table += end_table
table += end_figure

f.write(table)
f.close()




#pprint(link_direction_coarse_totals)
#pprint(allowedLabel)

errors = 0
total = 0
for coarse_label in link_direction_coarse_totals:
    direction = link_direction_coarse_totals[coarse_label]

    left = direction.get("left",0)
    right = direction.get("right",0)

    allowedDirection = allowedLabel[coarse_label]
    if not allowedDirection.get("0",False):
        errors += left
    if not allowedDirection.get("1",False):
        errors += right

    total += left + right


f = open(LABEL_TOKEN_DISALLOWED, "w+")
f.write(str(errors))
f.close()

f = open(LABEL_TOKEN_TOTAL, "w+")
f.write(str(total))
f.close()




match_percent = str(0)
if arc_total != 0:
    match_percent = str(int(float(match_total)/arc_total * 100 + 0.5))+ "\\%"
f = open(LATEX_FILE_CONLL_RECALL, "w+")
f.write(match_percent)
f.close()

match_precision = str(0)
if total != 0:
    match_precision = str(int(float(match_total)/total * 100 + 0.5)) + "\\%"
f = open(LATEX_FILE_CONLL_PRECISION, "w+")
f.write(match_precision)
f.close()

edge_percent = str(0)
edge_percent = str(int(float(total - arc_total) / float(arc_total) * 100 + 0.5)) + "\\%"
f = open(LATEX_FILE_EDGE_PERCENT, "w+")
f.write(edge_percent)
f.close()









#---------------------------------------------------------------------
# Sample coarse analysis/counts of the links, their labels, and their directions
# For the paper
#---------------------------------------------------------------------
SAMPLE_LATEX_FILE_COARSE_LINKS = LATEX_DIR+"sample_link_analysis_coarse_table.tex"
f = open(SAMPLE_LATEX_FILE_COARSE_LINKS, "w+")


# TODO use tabular
latex_table = "\\begin{tabular}{|l|l|l|l|l|l|}\n\\hline\n"
end_table = "\\end{tabular}\n"

header = "Label & Rightward & Multiheaded & CoNLL Match & CoNLL Dir Match & CoNLL Label\\\\"

begin_figure = "\\begin{small}\n\\centering\n"
end_figure = "\\end{small}\n"

def make_percentage_figure(top,bottom):
    return str(int(float(top) / float(bottom) * 100 + 0.5))+"\\%" + " ("+str(top)+"/"+str(bottom)+")"


table = begin_figure
table += latex_table

table += header + "\\hline\n"
#table += "\\endhead\n"
table += "\n"

#table += "\\hline\n\\endfoot\n\n"
table += "\\hline\n\n\n"

line = 0
for coarse_label in coarse_labels[:25]:
    count = link_label_coarse_counts[coarse_label]
    
    right = link_direction_coarse_totals[coarse_label].get("right",0)
    right = make_percentage_figure(right,count)

    prediction_num = ""
    prediction_total = ""
    match_percent = ""
    mismatch_percent = ""
    multiheaded = make_percentage_figure(link_label_isMultiheaded.get(coarse_label,0), count)


    prediction = coarse_predictions.get(coarse_label, "-")
    if prediction != "-":
        prediction_num = link_label_coarse_prediction[coarse_label][prediction]
        prediction_total = link_label_coarse_prediction_totals[coarse_label]
        prediction += " "+ make_percentage_figure(prediction_num, prediction_total)
        

    if prediction_num and prediction_total:
        match_percent = make_percentage_figure(prediction_total, count)

        mismatch_percent = make_percentage_figure((prediction_total - coarse_dir_mismatch.get(coarse_label,0)), prediction_total)


    else:
        match_percent = "-"
        mismatch_percent = "-"

    #table += "\\hline\n"
    table += coarse_label
    table += " & "+right
    table += " & "+multiheaded
    table += " & "+match_percent
    table += " & "+mismatch_percent
    table += " & "+prediction
    table += " \\\\ \n"
    line += 1
    
    # Break up the table into smaller tables
    """if line % 55 == 0:
        table += "\\hline\n"
        table += end_table
        table += end_figure
        table += begin_figure
        table += latex_table
        table += "\\hline\n"
        table += header
    """
table += "\\hline\n"
table += end_table
table += end_figure

f.write(table)
f.close()
