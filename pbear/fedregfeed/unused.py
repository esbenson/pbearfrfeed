

# --------------------------------------------------------------------------------------------------------------
#     list
#
#  shows a list of records in the local database
#
# --------------------------------------------------------------------------------------------------------------
def list_view(request, **kwargs):
    # search functionality is not implemented
    search_term = None

    # there should always be a display_num argument (i.e., number of items to display per page)    
    try:
        display_num=int(kwargs['display_num'])
        #print "display_num", display_num
    except KeyError:
        print "no display number argument found"
        raise Http404

    # get list of  docs matching search term, if there is a search term; otherwise get all
    #print "getting matching list of docs to search term (or all)"
    if search_term:
        doc_list = FedRegDoc.objects.filter(html_full_text__contains=search_term)
    else:
        doc_list = FedRegDoc.objects.all()

    # either get the requested doc_pk as first item to show ....  
    try:
        #print "trying to get doc_pk object"
        doc_pk=int(kwargs['doc_pk'])
        # for search, need to add check here for whether doc_pk is in search result set
        doc_list = doc_list.order_by('-publication_date')
        # got to be more efficient way to do the following! (i.e., find position of doc_pk object in date-ordered list)
        for display_offset in range(doc_list.count()):
            if doc_list[display_offset].pk == doc_pk:
                break
    # ...  or if no doc_pk given, show the most recent item
    except KeyError:
        #print "no doc_pk, instead retrieving most recent"
        # get the pk of the newest item by pub date
        doc_list = doc_list.order_by('-publication_date')
        doc_pk = doc_list[0].pk
        display_offset = 0
    total_doc_count = doc_list.count()        

    # set navigation parameters
    #print "total_doc_count", total_doc_count
    #print "setting nav parameters"
    if display_offset == 0:
        newest_pk=None
        newer_pk= None
    else:
        try:
            newest_pk = doc_list[0].pk
            newer_pk = doc_list[max(0, display_offset - display_num)].pk
        except IndexError:
            print "keyerror setting newest/er"
            raise Http404
    try:
        if (display_offset + display_num) >= total_doc_count:
            display_num = total_doc_count - display_offset + 1
            older_pk = None
            oldest_pk = None
        else:    
            older_pk = doc_list[min(total_doc_count - 1, display_offset + display_num)].pk
            oldest_pk = doc_list[max(0, total_doc_count - display_num)].pk
    except IndexError:
        print "keyerror setting oldest/er"
        raise Http404

    print "truncating list"
    # truncate doc_list to subset to display on this page   
    doc_list=doc_list[display_offset:(display_offset + display_num)]
                
    print "rendering"
    # render html via template
    return render_to_response('list.html', {"doc_list":doc_list, 'search_term':search_term, "doc_pk":doc_pk, "display_offset": display_offset, "display_num":display_num, "newest_pk":newest_pk, "newer_pk":newer_pk, "older_pk":older_pk, "oldest_pk":oldest_pk, "total_doc_count":total_doc_count}, context_instance=RequestContext(request))




# ------------------------------------------------
#    add html_full_text to database
#     (only if missing from record) 
#
#    this is meant to be a run-once function
#    to avoid reloading entire database
# ------------------------------------------------
#def add_html_full_text_to_all(request):
#    for d in FedRegDoc.objects.all():
#        print d.title
#        if not d.html_full_text:
#            try:
#                f=urlopen(d.html_url)
#                d.html_full_text=f.read()
#                f.close()
#                d.save()
#            except URLError:
#                print "URLError when opening ", d.html_url
#                
#    return render_to_response('add_html_full_text.html', {}, context_instance=RequestContext(request))





# NAV BLOCK REMOVED FROM DETAILS 
    # find primary key for nav to newer/newest record
    newest_pk = FedRegDoc.objects.order_by('-publication_date')[0].pk
    if newest_pk == doc.pk:
        newest_pk = None
        newer_pk = None
    else:
        q = list(FedRegDoc.objects.order_by('publication_date').filter(publication_date__gte = doc.publication_date).distinct())
        i = 0
        for i in range(len(q)):
            if q[i].pk == doc.pk:
                break
        try:
            newer_pk = q[i+1].pk
        except IndexError:
            newer_pk = None
            newest_pk = None

    # find primary key for nav to older/oldest record
    oldest_pk = FedRegDoc.objects.order_by('publication_date')[0].pk
    if oldest_pk == doc.pk:
        oldest_pk = None
        older_pk = None
    else:
        q = list(FedRegDoc.objects.order_by('-publication_date').filter(publication_date__lte=doc.publication_date).distinct())
        i = 0
        for i in range(len(q)):
            if q[i].pk == doc.pk:
                break
        try:
            older_pk = q[i+1].pk
        except IndexError:
            older_pk = None
            oldest_pk = None


