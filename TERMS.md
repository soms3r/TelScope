# TelScope Terms of Use

By downloading, installing, or using TelScope you agree to these terms.
If you do not agree, do not use it.

## 1. Authorized use only

TelScope is intended exclusively for:

- investigating **your own** phone numbers / email addresses;
- investigations where you hold **explicit written authorization** from the
  target or the target's organization (fraud teams, law enforcement, licensed
  investigators, penetration tests under contract);
- **legitimate security research** on publicly available data.

## 2. Prohibited use

You may not use TelScope for stalking, harassment, doxxing, domestic surveillance
without consent, identity theft, fraud, or any purpose that violates the law.
You may not use it to attempt unauthorized access to any account, system, or
platform, nor to circumstance authentication or security controls.

## 3. Third-party platforms

Wrapped modules rely on **publicly available data** and on platform
registration/recovery flows that reveal account existence without unauthorized
access. Those platforms' Terms of Service remain **your** responsibility.
Rate limits and anti-abuse signals surfaced by the tools (e.g. "rate-limited")
must be respected. Platform names are trademarks of their owners; TelScope is not
affiliated with or endorsed by any of them.

## 4. Outputs are leads, not facts

Findings (carrier, registrations, reputation scores) are probabilistic signals
for investigation support. They are **not proof** of identity, ownership, or
wrongdoing. Verify through proper channels before acting.

## 5. No warranty (MIT)

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. To the maximum
extent permitted by law, the authors and contributors of TelScope and of the
wrapped third-party tools shall not be liable for any claim, damages, or other
liability arising from your use of the software — including misuse against
third parties.

## 6. Legal compliance

Laws on data protection, privacy, and OSINT techniques differ by jurisdiction
(e.g. GDPR in the EU, local telecom privacy laws elsewhere). You are solely
responsible for complying with the laws that apply to you.

## 7. Third-party components

TelScope wraps six open-source tools that keep their own licenses, and adds six
built-in checks that use DNS, RDAP, libphonenumber and the Have I Been Pwned API
(see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)). The HIBP API requires your
own key and is subject to HIBP's terms. Use breach checks only for identifiers you
own or are authorized to check. Their use is additionally
governed by those licenses and their own terms.

## 8. Changes

These terms may be updated; the repository history is the record. Continued use
after changes constitutes acceptance.

*These terms are best-practice positioning for an open-source tool, not legal
advice. Consult a lawyer for commercial or sensitive deployments.*
