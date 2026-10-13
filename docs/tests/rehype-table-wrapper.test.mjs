import assert from "node:assert/strict";
import { test } from "bun:test";
import { rehypeTableWrapper } from "../src/shared/lib/markdown/rehype-table-wrapper.ts";

function makeTable() {
  return { type: "element", tagName: "table", properties: {}, children: [] };
}

function makeWrapper(className, table) {
  return {
    type: "element",
    tagName: "div",
    properties: { className },
    children: [table],
  };
}

test("wraps an unwrapped table with the table-wrapper class", () => {
  const table = makeTable();
  const tree = { type: "root", children: [table] };

  rehypeTableWrapper()(tree);

  assert.equal(tree.children[0].tagName, "div");
  assert.deepEqual(tree.children[0].properties.className, ["table-wrapper"]);
  assert.equal(tree.children[0].children[0], table);
});

test("leaves tables inside an existing wrapper with supported class forms", () => {
  const classNames = ["table-wrapper", "content table-wrapper", ["table-wrapper"], ["content", "table-wrapper"]];

  for (const className of classNames) {
    const table = makeTable();
    const wrapper = makeWrapper(className, table);
    const tree = { type: "root", children: [wrapper] };

    rehypeTableWrapper()(tree);

    assert.equal(tree.children[0], wrapper);
    assert.equal(wrapper.children[0], table);
  }
});

test("does not treat a similarly named class as the table wrapper", () => {
  const table = makeTable();
  const parent = makeWrapper(["table-wrapper-extra"], table);
  const tree = { type: "root", children: [parent] };

  rehypeTableWrapper()(tree);

  assert.equal(parent.children[0].tagName, "div");
  assert.deepEqual(parent.children[0].properties.className, ["table-wrapper"]);
  assert.equal(parent.children[0].children[0], table);
});
