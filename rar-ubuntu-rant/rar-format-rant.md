---
title: RAR file format and Linux - a silly rant
description: what bothers me about linux packaging and why it will never take off even among power users
# slug: hello
date: 2025-04-05T19:24:37+00:00
# image: cover.jpg
categories:
   - software
tags:
weight: 1       # You can add weight to some posts to override the default sorting (date descending)
---

I want to preface this by saying that I dont care about the whole "year of the linux desktop" stuff that this will eventually get into but the reality is, I daily drive linux on my personal device, so some minor stuff pisses me off. If I was to achieve this on windows, it wouldnt exactly be a cake walk either for the average user. Still, they'd have to download a program such as winrar or 7zip and then just be done with it.

What bothers me is I - or in this case - the average power user, if facing this scenario, would have to get into the terminal and apt install stuff. Yhat is just annoying, and not good ux. especially; not if you want to appeal to mass market users eventually.

## The actual problem - multi part archives in rar format

So, with the default file explorer, you cant extract multi part archives, there is a file roller app, but it doesnt have the unrar package.

Now, you must install it:

```shell
sudo apt install unrar
```

and now, you can unpack them with file roller! cool, but how the hell will "normal" users figure this out. They will end up installing bogus programs when they dont need to.
I guess, a lot of linux stuff is designed by developers for developers, which causes these things. The error message is not helpful at all: "too small block encountered 0 bytes" - what does this mean for the average user? I would just assume the rar file is corrupt!

There should be a way to do this without the user needing to meddle into the terminal!

Ideally, it should just say: "hey! you need to install this, click here", do it's thing and then let user get to whatever they are doing...

Maybe one day, it will be so simple. One day...
