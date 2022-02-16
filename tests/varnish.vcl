#
# This is an example VCL file for Varnish.
#
# It does not do anything by default, delegating control to the
# builtin VCL. The builtin VCL is called when there is no explicit
# return statement.
#
# See the VCL chapters in the Users Guide for a comprehensive documentation
# at https://www.varnish-cache.org/docs/.

# Marker to tell the VCL compiler that this VCL has been written with the
# 4.0 or 4.1 syntax.
vcl 4.1;

import std;

# acl for administrative requests (i.e BAN)
# Set this to the configured network between admin backend
# and varnish
acl purge {
  "172.199.0.0"/16; // Our backend network
}

# Default backend definition. Set this to point to your content server.
backend default {
    .host = "qgis-server";
    .port = "8080";
}

sub vcl_recv {
    # Happens before we check if we have this in cache already.
    #
    # Typically you clean up the request here, removing cookies you don't need,
    # rewriting the request, etc.

    # Handle BAN request
    if (req.method == "BAN") {
        if (!client.ip ~ purge) {
            return(synth(405,"Not Allowed"));
        }
        if (std.ban("obj.http.X-Map-Id ~ " + req.http.X-Map-Id)) {
            return(synth(200,"Ban Added"));
        } else {
            return(synth(400, std.ban_error()));
        }
    }
}

sub vcl_backend_response {
    # Happens after we have read the response headers from the backend.
    #
    # Here you clean the response headers, removing silly Set-Cookie headers
    # and other mistakes your backend does.

    # Set grace period long enough to get 
    # the response from long loading projects 
    set beresp.grace = 10m;

    # Keep the response in cache for 24 hours if the response has
    # validating headers.
    if (beresp.http.ETag || beresp.http.Last-Modified) {
        set beresp.keep = 24h;
    }

    return (deliver);
}

sub vcl_deliver {
    # Happens when we have all the pieces we need, and are about to send the
    # response to the client.
    #
    # You can do accounting or modifying the final object here.
}

