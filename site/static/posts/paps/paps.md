# Why are pre-analysis plans good?

From the classic statistical perspective pre-analysis plans (PAPs) are a bit weird. Why would the researcher pre-register a plan when, after receiving the data, they might learn important things which can improve their study?

We can only see an answer once we realize that researchers are not just pursuing the ideal of truth, but also competing in the cut-throat academic market, and as such their incentives are not to figure out whats true, but rather to get publishable results.[^1] Pre-analysis plans are one way to align these goals, as [Kasy and Spiess](https://arxiv.org/abs/2208.09638) [1] argue in a recently revised paper. I like this paper! But this post is about elements of PAPs which they don't discuss that I think are essential to understanding when PAPs work and when they don't. You don't have to have read their paper to read this post, it should stand on its own (but the paper is very readable!).

The tl;dr is that PAPs are great when the estimator is guaranteed to be consistent since they allow the researcher to use complex analysis pipelines. But when the estimator might be inconsistent it's unclear whether or how PAPs are helpful at all!

Now, before diving in its worth stepping back: PAPs are a relatively recent innovation, so how did social scientists manage these misaligned incentices before they were widespread?

One way was by forcing everyone to use linear regression.[^2] The simplicity of linear regression allows practitioners to have clear intuitions about what is reasonable in any given study. If we imagine that the workhorse of social science was random forests, where there are many tuning parameters which matter a lot to the kinds of results you get, we would be much more worried that researchers tried every possible tweak to get the results they want.[^3] I'll call this kind of p-hacking specification searching, and its the main thing I'm focused on in this post.

Specification search is less of a problem in linear regression because there are fewer degrees of freedom. Restricting research to use linear regression is a way to try to constrain researchers to produce "true" rather than merely "statistically significant" findings. It is an imperfect way to try to align researchers with the knowledge-seeking ideal, and one that comes with a lot of costs, but combined with adversarial peer review it is current best practice in observational social science.

Pre-analysis plans emerge as an alternative in experimental settings. Instead of having to use a simple tool (like linear regression) pre-analysis plans allow using complex tools as long as all the dials are set in advance of seeing the data. So now the researcher can pre-register a random forest specification and then reviewers can be confident they didn't tune the parameters to get the results they want.

That's the real trick: **PAPs free us from linear regression.** They decouple the complexity of a research design from the researchers ability to p-hack. So PAPs enable researchers use sophisticated econometric techniques without running into the problem of reviewer's (often reasonable!) disbelief.

The more common way of pitching PAPs is by saying they control p-hacking and specification search. I think this is not a particularly useful way to think about PAPs, since PAPs only "solve" these problems in very specific situations, as I'll demonstrate below.

Now returning to Kasy and Spiess, they provide a fully game theoretic formulation PAPs and built on top of a particular statistical model. But the statistical model at the heart of their formulation seems to make it hard to see some of my central issues with PAPs.

These issues become clear if we think about a simple model of specification search. We will consider an experiment where we are interested in estimating the ATE and we will see that the Kasy and Spiess results are plausible, even if its unclear whether it is actually compatible with their formulation. Then we will change the estimand to a linear heterogeneous treatment effect and everything will fall apart.

My point is that you only perform a specification search if there is not an a prori correct specification. So to understand PAPs you need to allow the possibility of mis-specification. Sometimes mis-specification is not a problem (as in the ATE case), and sometimes it is (as in the HETE case).

But this will bring us back to the benefit of PAPs I outline above: we can pre-specify more complex, more flexible research designs that can try to mitigate the possibility of misspecification. Now this does not completely dissolve the issue: no matter how smart we are about our statistics/econometrics it is always possible the data confounds our priors and our pre-specified plan ends up seeming naive ex post. I think this is maybe the most interesting statistical question about PAPs: how do we think about ex post changes or adaptations?

Now on to the math!

## A simple experiment - the consistent case

A researcher has a population of individuals with $p$-dimensional covariates vectors $X_i$. They run an experiment, randomly assigning treatments $T_i \sim \text{Bern}(\frac12)$ to the population. After the experiment they observe an outcome $Y_i$.

We can assume a simple linear model for the outcome:

$$Y_i = \tau T_i + \beta X_i + \epsilon_i$$

Where $\epsilon_i$ is some iid noise. The researcher wants to maximize their probability of rejecting the null $H_0: \tau = 0$ in favor of the alternative $H_1: \tau \neq 0$.

We will assume throughout that researchers are restricted to running ordinary least squares to estimate their effects. This will illustrate the dynamics of misspecification I discuss above, and we will generalize all these intuitions below.

Since the researcher randomized $T_i$ they can just consider the truncated regression:

$$ Y_i = \tau T_i + \epsilon'_i$$
And this is a consistent estimator (since $T_i \perp X_i, Y(0), Y(1)$). But this will not maximize the chance they reject the null.

If the researcher does not pre-register their analysis they might search over all possible linear regressions, running the regression $Y_i = \tau T_i + \beta_S S_{i} \epsilon'_i$ for every subset $S_i$ of $X_i$, picking the subset of covariates to include that results in the smallest p-value for $\hat \tau$. This will invalidate the hypothesis test,[^4] so instead we can force the researcher to pre-register the subset of covariates they will include in the regression $S$.

Now if we assume $\beta$ is sparse the researcher's problem is a little tricky. To maximize their power they want to include only the non-zero components of $\beta$, but they don't know which components those will be.

It is worth noting that the researcher can pre-specify any subset of covariates and have a _consistent_ estimator for $\tau$, the only thing thats tricky is maximizing their power. So if we assume the researcher has some prior over which subests of $X_i$ are likely to be non-zero, its straightforward to see that they will pre-register their best-guess.

I do not think this model is quite covered by the Kasy and Spiess paper, which is a bit sad, but its very obviously in the spirit of the results they derive.

Now there is a very obvious issue here: if we assume $\beta$ is sparse and the researcher only cares about $\tau$ they should simply pre-register an L1 penalty on $\beta$ in their linear regression. Then using standard semi-parametric results they can build confidence intervals for $\tau$ and they should be able to directly maximize their power. This _requires_ deviating from the standard linear regression, but since it's preregistered we don't have to worry about the increased number of researcher degrees of freedom involved, since those are all fixed independently of the data (since they are chosen before the researchers sees the data).

## Heterogeneous treatment effects - the inconsistent case

Now lets break things. Let us add a set of new covariates $Z_i$ to our model and consider the case where the researcher is interested in the heterogenous treatment effect:

$$Y_i = \tau T_i + \beta X_i + \zeta Z_i + \gamma T_i Z_i + \epsilon_i $$

Where the researcher wants to test the null $H_0: \gamma = 0$ against $H_1: \gamma \neq 0$. But we have not imposed restrictions on $\text{Cov}(X_i, Z_i),$ so in general these covariates can have arbitrary dependence.

Here our restriction to ordinary least squares creates a serious problem.

What will the researcher do? It seems like their best hope is to pre-register a specification they think has the highest likelihood of being correct, knowing that it might not be realized. Then they get the data and it might become clear that their pre-registered specification is incorrect and again via specification search they might find a specification they think is “better”.

In the previous case the mis-specification was only a problem for the researcher. It hurt their power, but the reviewer is willing to give up on some theoretical power since it lets the reviewer guarantee that the researcher is performing valid statistical tests (I think this is the core intuition [1] is trying to formalize).

In this case the mis-specification is a problem for the reviewer too, since if the researcher fails to include a covariate $X_j$ which has a non-zero coefficient $\beta_{j}$ then the researcher's test for $\gamma = 0$ will be invalid.

This seems like the real objection to pre-analysis plans: that what the researcher preregistered was their “best guess” at what the right specification was, but they might be wrong! They might look at the estimated $\gamma$ and think that it is very surprising, e.g. it is insignificant with the wrong sign, which might prompt them to look at the data again only to realize this surprisingness is because they left out an important covariate in their pre-analysis plan which, when included, brings the estimated $\gamma$ in line with their prior.

The problem is that to the reviewer this is observationally equivalent to the case where the researcher just tried every possible regression until they got a significant result.

So what should we do here? Well again the obvious answer, under the particular model in this case, is to once more use an L1 penalty and include all covariates, using semi-parametrics to ensure a valid unbiased estimator for $\gamma$. And that's the point! Double-debiased machine learning has a lot of dials we might worry about researchers tweaking in observational settings, but PAPs completely ameliorate these issues because PAPs force these degrees of freedom to be fixed before the researcher gets the data.

But it's also worth noting that our L1 penalized model can be mis-specified too. It might be that there are pairwise interactions, or three-way interactions. At some point we have to make assumptions to make inference feasible. But those assumptions might be wrong, and it might be obvious they are wrong only after the fact. How should we handle this? Theoretically its very thorny, but maybe in practice its simple: researchers will explain why the PAP was wrong and argue the new specification is better, and reviewers will decide whether this is reasonable. Developing some theory to guide this process would be very useful though!

## Generalizing these results

I focused on the linear regression case above, but the cases above can be made fully general by considering misspecification with an always consistent estimator and a possibly inconsistent estimator. In the first case we only have concerns about power while in the second we have more serious concerns about whether we are testing the right null hypothesis. In the first case the reviewer gets to control specification search while getting a valid statistical test. In the second the researcher learns the pre-specified model is wrong, and so specification search is essentially necessary, but the researcher cannot tell whether the researcher is searching for the "true" model or just a model that rejects the null. Maybe the researcher cannot tell either.

Whatever model we posit could be wrong in a way we might not be able to explain a priori but becomes more clear a posteriori. This is a real issue with pre-analysis plans especially when researchers are restricted to “simple” designs, but it carries over to more complex procedures as well.

## Conclusion

The central takeaway here is that pre-analysis plans enable arbitrarily complex statistical procedures to be admissible strategies in the researcher-reviewer game. The obvious solution to the particular problems above is “use the right model rather than restricting yourself to OLS”. But social scientists have been trained (I would argue reasonably) to not trust methods with too many degrees of freedom. This is necessary if researchers are not using PAPs since too giving researchers too many dials to turn makes the problem of specification search much harder to detect and ameliorate as a reviewer (and it is already very hard!).

When our estimator is _consistent_ PAPs are magic: since they completely restrict the researcher ex ante this issue goes away completely. But when our estimator might be _inconsistent_ its not clear PAPs can guarantee us very much at all.

The centrality of consistency and complexity seem like really important points to me! And these are points which cannot really be made in Kasy and Spiess given the way they have set up their model.

A last point worth making here is that all of this makes experiments+PAPs really exciting for econometricians and statisticians! Unfortunately even if a researcher could specify the correct model deriving “the right test” is often hard. The semiparametrics necessary to ensure a consistent estimator with correct confidence intervals for $\gamma$ in the second case is not trivial! And this remains a very stylized linear model! This "problem" is great for econometricians and statisticians who have specialized in nailing the estimator, given the model. Opportunities for important collaborations abound!

## References

[1] Kasy, Maximilian, and Jann Spiess. "Rationalizing Pre-Analysis Plans: Statistical Decisions Subject to Implementability." [_arXiv preprint arXiv:2208.09638_](https://arxiv.org/abs/2208.09638) (2022).

[^1]: The miracle of science is that these two goals are not that misaligned: journals and peer reviewers, universities, and grant making institutions conspire to ensure that "good" physics or chemistry or biology are rewarded. But those are the easy sciences, where signal tends to be high relative to noise and experiments tend to be easily repeatable regardless of context.

[^2]: This is not the only reason social scientists use OLS. In practice it is likely primarily inertia. But I think it does control degrees of freedom nonetheless and so this rationalization is reasonable. 

[^3]: At least for the specification search problem in linear regression the chosen covariates have to appear in the regression equation! The transparency element is probably very important here, as if not more so than the degrees of freedom perspective since it allows peer review to function.

[^4]: Surprisingly some back of the envelope math and simulations imply this kind of specification search does not actually inflate the Type I error very much unless $p >> n$. For $n=500$ and $p=10,000$ and setting the significance level $\alpha=0.05$ the actual probability of accepting the null is $0.1$.

