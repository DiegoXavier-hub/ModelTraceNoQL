/**
 * Helpers para extrair nomes/identificadores de entidades de predições e casos,
 * filtrando o sentinel "[protected]" que o backend devolve quando a chave de
 * descriptografia não está disponível ou quando ``redact_pii=true``.
 *
 * Usuário autenticado deve sempre ver os valores reais — o backend já passa
 * por ``reveal_entity`` antes de devolver. Esta função é a última linha de
 * defesa cosmética para evitar exibir o sentinel se algum endpoint voltar
 * direto do storage por engano.
 */

const PROTECTED_SENTINELS = new Set(["[protected]", "[redacted]", "[masked]"]);

export function cleanProtectedValue(value?: unknown): string {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  if (!text) return "";
  if (PROTECTED_SENTINELS.has(text)) return "";
  return text;
}

interface EntityShape {
  display_name?: unknown;
  id?: unknown;
  id_masked?: unknown;
  [key: string]: unknown;
}

/**
 * Devolve o melhor nome disponível para uma entidade, na ordem:
 *   display_name → id → id_masked → fallback
 *
 * Cada candidato passa por ``cleanProtectedValue`` antes, evitando o sentinel.
 */
export function entityDisplayName(entity?: EntityShape | null, fallback: string = "Entidade"): string {
  if (!entity) return fallback;
  const candidates = [entity.display_name, entity.id, entity.id_masked];
  for (const candidate of candidates) {
    const cleaned = cleanProtectedValue(candidate);
    if (cleaned) return cleaned;
  }
  return fallback;
}

/**
 * Devolve o identificador legível (não-mascarado) preferindo ``id`` real.
 * Útil para exibir abaixo do nome em fonte mono.
 */
export function entityIdentifier(entity?: EntityShape | null): string {
  if (!entity) return "";
  return cleanProtectedValue(entity.id) || cleanProtectedValue(entity.id_masked);
}
