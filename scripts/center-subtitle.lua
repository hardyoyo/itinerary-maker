-- Center the subtitle (the first paragraph that is just italic text)
-- for LaTeX/PDF output only; HTML keeps it left-aligned.

local centered = false

return {
  {
    Para = function(el)
      if centered or FORMAT ~= "latex" then
        return nil
      end
      if #el.content == 1 and el.content[1].t == "Emph" then
        centered = true
        local inner = pandoc.write(pandoc.Pandoc(pandoc.Para(el.content[1].content)), "latex"):gsub("^%s+", ""):gsub("%s+$", "")
        return pandoc.RawBlock("latex", "\\begin{center}\n" .. inner .. "\n\\end{center}")
      end
    end,
  },
}