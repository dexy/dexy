library(tools)
library(rjson)

if (length(packages) == 0) {
    stop("no packages!")
}

# Set up 1 environment to store all data, this will be written to JSON at the end.
packages_info <- new.env(hash=TRUE)

# This function will do the real work of extracting content.  It should return
# a list of lists each with 2 entries, the section name and the content for
# that section. Many sections will just return 1 such list, but sometimes we
# will want to process a section in multiple ways, e.g. format hyperlinks for
# both HTML and LaTeX, so we expect to return a list of lists to account for
# this.
processSection <- function(content, tag) {
    result <- switch(tag,

                     "\\alias"=processSimple(content),
                     "\\arguments"=processArguments(content),
                     "\\author"=processSimple(content),
                     "\\description"=processSimple(content),
                     "\\details"=processSimple(content),
                     "\\examples"=processExamples(content),
                     "\\keyword"=processSimple(content),
                     "\\name"=processSimple(content),
                     "\\note"=processSimple(content),
                     "\\references"=processSimple(content),
                     "\\section"=processSubSection(content),
                     "\\seealso"=processSimple(content),
                     "\\source"=processSimple(content),
                     "\\title"=processSimple(content),
                     "\\usage"=processUsage(content),
                     "\\value"=processSimple(content),

                     # default case
                     stop(paste("I don't know how to handle tag '", tag, "'", sep=""))
                     )
    return(result)
}

stripLeadingTrailingWhitespace <- function(s) {
    s <- gsub('[[:space:]]+$', ' ', s)
    s <- gsub('^[[:space:]]+', ' ', s)
    return(s)
}

stripLeadingTrailingSpaceAbsolute <- function(s) {
    s <- gsub('[[:space:]]+$', '', s)
    s <- gsub('^[[:space:]]+', '', s)
    return(s)
}

fixDoubleSpaces <- function(s) {
    return(gsub('\\s+', ' ', s))
}

sep <- function() {
    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
}

processSubSection <- function(content) {
    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
    }
    return(list(list("section", "blah")))
}

processUsage <- function(content) {
    usage_content <- c()
    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
        if (item_tag %in% c("\\method", "\\S4method", "\\S3method")) {
            usage_content <- c(usage_content, item[[1]][[1]]) # dropping 2nd element, could also join with "."
        } else if (item_tag %in% c("RCODE", "\\dots")) {
            usage_content <- c(usage_content, item)
        } else {
            stop(paste("I don't know how to handle tag '", item_tag, "' in usage", sep=""))
        }
    }
    return(list(list("usage", stripLeadingTrailingWhitespace(paste(usage_content, sep="", collapse="")))))
}

processExamples <- function(content) {
    examples <- list()
    all_examples <- list()
    dontrun_examples <- list()

    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
        example_content <- processExample(item)

        if (length(grep("^[[:space:]]*$", example_content)) > 0) {
            next # skip this blank line
        }

        if (item_tag %in% c("RCODE", "\\S4method", "\\method", "\\testonly")) {
            examples[[length(examples) + 1 ]] <- example_content
            all_examples[[length(all_examples) + 1 ]] <- example_content
        } else if (item_tag %in% c("\\dontrun", "\\donttest")) {
            dontrun_examples[[length(dontrun_examples) + 1 ]] <- example_content
            all_examples[[length(all_examples) + 1 ]] <- example_content
        } else {
            stop(paste("I don't know how to handle tag '", item_tag, "' in examples", sep=""))
        }
    }

    label <- "examples"
    return_examples <- list(label, examples)
    return_dontrun_examples <- list(paste(label, "dontrun", sep="-"), dontrun_examples)
    return_all_examples <- list(paste(label, "all", sep="-"), all_examples)
    return(list(return_examples, return_dontrun_examples, return_all_examples))
}

processExample <- function(content) {
    return(paste(content, sep="", collapse=""))
}

processArguments <- function(content) {
    arguments_list <- list()
    for (item in content) {
        item_tag <- attr(item, "Rd_tag")
        result <- switch(item_tag,
                         TEXT=NA,
                         "\\item"=processArgument(item),

                         # default case
                         stop(paste("I don't know how to handle tag '", item_tag, "' in arguments"))
                         )

        if (!is.na(result)) {
            arguments_list[result[[1]]] <- result[[2]]
        }
    }
    return(list(list("arguments", arguments_list)))
}

processArgument <- function(content) {
    argument_name <- processSimpleChunk(content[[1]][[1]])
    argument_info <- stripLeadingTrailingSpaceAbsolute(paste(lapply(content[[-1]], processSimpleChunk, TRUE), sep="", collapse=""))
    return(list(argument_name, fixDoubleSpaces(argument_info)))
}

# Use this when we don't need any fancy processing.
processSimple <- function(content) {
    section_tag <- attr(content, "Rd_tag")
    clean_tag <- strsplit(section_tag, "\\", fixed=TRUE)[[1]][[2]]

    processedContent <- paste(lapply(content, processSimpleChunk), sep="", collapse="")
    basic_entry <- list(clean_tag, fixDoubleSpaces(processedContent))
    return(list(basic_entry))
}

# Checks to make sure the data type is appropriate for simple processing,
# returns the chunk's content unchanged.
processSimpleChunk <- function(chunk, stripExtraWhitespace=TRUE) {
    chunk_description <- attr(chunk, "Rd_tag")
    result <- switch(chunk_description,
                     "\\R"="R",
                     "\\S4method"=chunk,
                     "\\code"=chunk,
                     "\\command"=chunk,
                     "\\dQuote"=chunk,
                     "\\describe"=chunk,
                     "\\dots"=chunk,
                     "\\email"=chunk,
                     "\\emph"=chunk,
                     "\\enumerate"=chunk,
                     "\\env"=chunk,
                     "\\eqn"=chunk,
                     "\\file"=chunk,
                     "\\item"=chunk,
                     "\\itemize"=chunk,
                     "\\link"=chunk,
                     "\\method"=chunk,
                     "\\option"=chunk,
                     "\\pkg"=chunk,
                     "\\preformatted"=chunk,
                     "\\sQuote"=chunk,
                     "\\samp"=chunk,
                     "\\tabular"=chunk,
                     "\\url"=chunk,
                     "\\var"=chunk,
                     "\\verb"=chunk,
                     CODE=chunk,
                     COMMENT=chunk,
                     LIST=chunk,
                     RCODE=chunk,
                     TEXT=chunk,
                     VERB=chunk,

                     # default case
                     stop(paste("I don't know how to handle data type '", chunk_description, "'", sep=""))
                     )
    if (length(result) == 0) {
        result = ""
    }
    if (stripExtraWhitespace) {
        result <- stripLeadingTrailingWhitespace(result)
    }
    return(result)
}

# Main loop in which we gather content by iterating over packages, Rd files
# within packages and tags within Rd files.
for (pkg_name in packages) {
    # Load the package, so we can obtain source code from methods.
    require(pkg_name, character.only = TRUE, keep.source = TRUE)

    # Get the stored Rd files for this package.
    db <- Rd_db(pkg_name)

    # Set up an environment in which to store collected data.
    pkg_info <- new.env(hash=TRUE)

    # Pre-process each Rd chunk.
    Rd_list <- lapply(db, tools:::prepare_Rd)
    tags_list <- lapply(Rd_list, tools:::RdTags)

    # Get the canonical name for each Rd file.
    names <- lapply(db, tools:::.Rd_get_metadata, "name")

    for (f in names(db)) {
        # Get the data corresponding to this file.
        Rd <- Rd_list[[f]]
        tags <- tags_list[[f]]

        # Set up an environment for this file's info.
        file_info <- new.env(hash=TRUE)

        # Store the info we want in the environment.
        assign("filename", f, env=file_info)

        if (exists(names[[f]])) {
            f_closure <- get(names[[f]])
            source_code <- paste(deparse(f_closure), collapse="\n")
            assign("source", source_code, env=file_info)
        }
        for (i in seq_along(tags)) {
            results <- processSection(Rd[[i]], tags[[i]])
            for (result in results) {
                assign(result[[1]], result[[2]], env=file_info)
            }
        }

        # Add this file's environment to the package's overall environment.
        assign(names[[f]], file_info, env=pkg_info)
    }

    # Detach this package now that we are done with it.
    name_with_pkg <- paste("package", pkg_name, sep=":")
    detach(name_with_pkg, character.only = TRUE)

    # Add the pkg_info environment to the overall environment for all packages.
    assign(pkg_name, pkg_info, env=packages_info)
}

data_file <- file("dexy--r-doc-info.json", "w")
writeLines(toJSON(as.list(packages_info)), data_file)
close(data_file)

