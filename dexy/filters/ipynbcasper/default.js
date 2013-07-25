// Script template - will have string interpolation applied.
var casper = require('casper').create({
    viewportSize : {width : %(width)s, height: %(height)s }
});

casper.start("http://localhost:%(port)s", function() {
    this.waitForSelector("#notebook_list");
});

casper.then(function() {
    this.capture('notebook-list.png');
});

casper.run();
