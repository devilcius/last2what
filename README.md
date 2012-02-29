#last2what
A python module to update what.cd missing artist infos


### dependencies

whatapi - https://github.com/devilcius/whatapi
pylast - http://code.google.com/p/pylast/

### installation
    
create a config file, name it last2what.cfg, put it in the last2what dir with the following content:
    
<pre>
    
[what]
username = 
password = 

[connection]
proxyenabled = 0
proxyserver = 
proxyport = 

[last]
# this is the sample key provided by last.fm
apikey = b25b959554ed76058ac220b7b2e0a026
    
</pre>

and fill the missing values.
    
### Usage (at your own risk)

    $ python last2what.py -h
