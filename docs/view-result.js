function toggle_result_block(e) {
  this.prev().toggleClass('stacked');
  this.toggle();
  return false;
}

function insert_result_links() {
  $('.result').each(function(idx, node) {
    znode = $(node);
    icon = znode.prev().find('i')
    icon_link = icon.parent('a')
    var clickfn = $.proxy(toggle_result_block, znode);
    icon_link.on('click', clickfn);
    clickfn();
  });
}

$(insert_result_links);
