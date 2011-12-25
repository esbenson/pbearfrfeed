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

