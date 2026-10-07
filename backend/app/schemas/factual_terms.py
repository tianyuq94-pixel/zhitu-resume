"""Distinguish English prose from technical claims in generated feedback."""
import re

TECHNOLOGIES = set('''python javascript typescript java kotlin swift golang rust ruby php
react vue angular next.js nuxt.js svelte fastapi django flask spring node.js express
mysql postgresql sqlite mongodb redis elasticsearch kafka rabbitmq docker kubernetes
linux windows macos tensorflow pytorch keras numpy pandas scipy scikit-learn opencv
html css sass tailwind bootstrap aws azure gcp git github gitlab jenkins terraform
sql nosql graphql rest grpc http https api sdk llm rag lora bert gpt deepseek
blender maya zbrush autocad unity unreal ue5 figma photoshop comfyui midjourney'''.split())


def technical_terms(text: str) -> set[str]:
    terms = set()
    for token in re.findall(r'[A-Za-z][A-Za-z0-9.+#-]*', text):
        cleaned = token.rstrip('.').casefold()
        if cleaned in TECHNOLOGIES or re.search(r'[a-z][A-Z]', token) or (token.isupper() and len(token) > 1 and token not in {'CV', 'STAR', 'AI'}):
            terms.add(cleaned)
    return terms


ENGLISH_CONNECTIVES = set('''a an the and or but with without through to of for from in on
at by as is are was were be been being it its this that these those my our their your
which who while when where then also both each into across using used use applying
applied apply implementing implemented implement developing developed develop building
built build creating created create managing managed manage supporting supported support
delivering delivered deliver improving improved improve designing designed design'''.split())
