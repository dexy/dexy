var casperDefaults = {
    viewportSize : {width : %(width)s, height: %(height)s },
    verbose: true,
    logLevel: "debug"
};

var casper = require('casper').create(casperDefaults);

/* debugging util */
function printObject(obj) {
    for (var attr in obj) {
        console.log(attr + ": " + obj[attr]);
    }
}

var rootUrl = "http://localhost:%(port)s";

var hrefs;
var names;

casper.start(rootUrl, function() {
    this.waitForSelector("#notebook_list");
});

casper.then(function() {
    hrefs = this.getElementsAttribute('#notebook_list .list_item a.item_link', 'href');
    names = this.getElementsInfo('#notebook_list .list_item a.item_link .item_name');
});

function cellSelector(j) {
    return "#notebook-container>.cell:nth-child(" + (j+1) + ")";
}

function runCurrentCell(j) {
    var inputPromptSelector = cellSelector(j) + " .input_prompt";
    var cellMenuSelector = "ul#menus li.dropdown:nth-child(5)";
    var dropDown = cellMenuSelector + ">.dropdown-menu";

    casper.then(function() {
        //this.test.assertSelectorHasText(cellMenuSelector, "Cell");
        //this.test.assertNotVisible(dropDown);
        this.click(cellMenuSelector + " a");

        //this.test.assertVisible(dropDown);
        //this.test.assertSelectorHasText("#run_cell a", "Run");
        this.click("#run_cell a");

        //this.test.assertNotVisible(dropDown);

        this.waitFor(function cellMarkedAsRunning() {
            return (this.getElementsInfo(cellSelector(j))[0].attributes['class'].indexOf("running") < 0);
        });
    });

    casper.then(function() {
        if (this.exists(inputPromptSelector)) {
            this.waitFor(function codeCellNotRunning() {
                return (this.getElementsInfo(inputPromptSelector)[0].text.indexOf("[*]") < 0);
            }, function() {}, function() {}, %(cell_timeout)s);
        }
    });
}

function openNotebook(name, href) {
    console.log("Calling openNotebook with " + name + ", " + href);

    casper.thenOpen(rootUrl + href, function() {
        casper.waitForSelector("#notebook-container");
    });

    casper.then(function() {
        // wait for css/mathjax to finish loading
        // TODO figure out how to do this correctly
        this.wait(1000);
    });

    /// @export "cells-loop"
    casper.then(function() {
        cells = this.getElementsInfo('#notebook-container .cell');

        for (var j = 0; j < cells.length; j++) {
            console.log(j);
            runCurrentCell(j);
        }

        // Iterate over a second time to take screenshots - need to do in
        // separate loop to ensure that runCurrentCell finishes.
        for (j = 0; j < cells.length; j++) {
            var cell_image_name = name + "--" + j + "%(ext)s";
            this.captureSelector(cell_image_name, cellSelector(j));
        }
    });

    /// @export "capture-notebook"
    casper.then(function() {
        this.captureSelector(name + "%(ext)s", "#notebook-container");
    });
    /// @end
}

casper.then(function() {
    for (var i = 0; i < names.length; i++) {
        openNotebook(names[i].text, hrefs[i]);
    }
});

casper.run();
