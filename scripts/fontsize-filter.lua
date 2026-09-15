-- Convert <span style="font-size:Npx"> (or Npt) into LaTeX \fontsize{N}{...}\selectfont
-- at the target size, so the PDF keeps the sizes without embedding them as plain text.
-- Only applies to LaTeX (PDF) output; HTML keeps the CSS font-size spans as-is.

local function is_latex()
  return FORMAT:match("latex") ~= nil
end

local function fontsize_pt(style)
  return tonumber(style:match("font%-size:%s*(%d+)%s*pt"))
end

return {
  {
    Span = function(el)
      if not is_latex() then
        return nil
      end
      local pt = fontsize_pt(el.attributes.style or "")
      if not pt then
        return nil
      end
      local open  = pandoc.RawInline("latex", "{\\fontsize{" .. pt .. "}{" .. math.floor(pt * 1.2) .. "}\\selectfont ")
      local close = pandoc.RawInline("latex", "}")
      local out   = { open }
      for _, v in ipairs(el.content) do
        table.insert(out, v)
      end
      table.insert(out, close)
      return out
    end,
  },
}