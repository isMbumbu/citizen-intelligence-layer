# Finance specification

Budget concepts remain distinct in `FinancialRecord`: allocated, committed,
contracted, spent, and reported. Every record stores its currency, financial
period, and a claim that supports the displayed value. The project detail
endpoint highlights allocated, contracted, and spent while also returning any
committed and reported amounts that are available.

A contract is a separate record linked to a contractor identity. Its value is
represented as a contracted financial record rather than reducing all finance
to a single project amount.
