/** Fills {{var}} placeholders with an instance's numbers; unknown names are left as-is. */
export function fillTemplate(text: string, vars: Record<string, string>): string {
  return text.replace(/\{\{(\w+)\}\}/g, (match, name: string) => vars[name] ?? match)
}
